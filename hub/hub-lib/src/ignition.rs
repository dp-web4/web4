//! Held ignition's seal (hub/docs/PRD_HELD_IGNITION.md §3.2): a copy of the vault passphrase,
//! sealed by `systemd-creds --user` and read back by the hub at boot. A host-key seal relies on
//! host-secret custody plus the UID, username, and machine ID: a full copy carrying those values
//! and the secret can carry decryption capability to another machine. TPM-backed tiers also
//! require the original TPM chip; the measured pcr_mask 0 does not attest to the boot state.
//!
//! The tier is read from the sealed file, never from the flag that asked for it. In `--user` mode
//! systemd chooses the key itself: on HUB a `host+tpm2` request came back host-only, and on pub a
//! `host` request came back host+tpm2 (both measured 2026-10-30). So the hub seals with `auto` and
//! then reads the seal id, the first 16 bytes of the decoded file.

use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use anyhow::{anyhow, bail, Context, Result};
use base64::Engine;
use zeroize::Zeroizing;

use crate::events::IgnitionRelease;
use crate::law::{IgnitionPolicy, IgnitionTier};

/// The sealed passphrase, in the hub directory.
pub const IGNITION_FILE: &str = "ignition.cred";
/// The name the seal is bound to: a file renamed to seal something else won't open as this.
const SEAL_NAME: &str = "hub-ignition";

/// Seal ids measured on real hosts (systemd 259; the ids are constants in systemd's
/// `src/shared/creds-util.h`). Only measured ids are here: any other id is
/// [`IgnitionTier::Unknown`], which meets no `min_tier` ([`IgnitionTier::meets`]), so it is never held.
const MEASURED_SEALS: [([u8; 16], IgnitionTier); 2] = [
    // HUB, 2026-10-30: `--user`, no TPM driver. User-scoped, host key only.
    (
        [0x55, 0xb9, 0xed, 0x1d, 0x38, 0x59, 0x4d, 0x43, 0xa8, 0x31, 0x9d, 0x2e, 0xbb, 0x33, 0x2a, 0xc6],
        IgnitionTier::HostKey,
    ),
    // pub, 2026-10-30: `--user`, a real TPM. User-scoped, host key and TPM2 (pcr_mask 0: bound
    // to the chip, not to a measured boot).
    (
        [0xef, 0x4a, 0xc1, 0x36, 0x79, 0xa9, 0x48, 0x0e, 0xa7, 0xdb, 0x68, 0x89, 0x7f, 0x9f, 0x16, 0x5d],
        IgnitionTier::HostTpm2,
    ),
];

/// The path of the sealed passphrase for the hub at `hub_dir`.
pub fn ignition_path(hub_dir: &Path) -> PathBuf {
    hub_dir.join(IGNITION_FILE)
}

/// Where a new seal is written before its hold is recorded. Boot reads only [`ignition_path`], so
/// a copy here can never be booted from; it is renamed into place only after `IgnitionHeld` is on
/// the ledger (NOVA, #970), and a leftover one is deleted at the next unlock.
pub fn staged_ignition_path(hub_dir: &Path) -> PathBuf {
    hub_dir.join(format!("{IGNITION_FILE}.staged"))
}

/// The tier of a sealed file, from its seal id. Anything unreadable is `Unknown`.
pub fn tier_of_sealed(sealed: &[u8]) -> IgnitionTier {
    // 24 base64 characters decode to exactly 18 bytes, which cover the 16-byte id.
    let head: Vec<u8> = sealed.iter().copied().filter(|b| !b.is_ascii_whitespace()).take(24).collect();
    let Ok(raw) = base64::engine::general_purpose::STANDARD.decode(&head) else {
        return IgnitionTier::Unknown;
    };
    MEASURED_SEALS
        .iter()
        .find(|(id, _)| raw.get(..16) == Some(&id[..]))
        .map_or(IgnitionTier::Unknown, |(_, tier)| *tier)
}

/// Whether the law `policy` rejects the sealed copy held at `hub_dir`, and why. `None` only when
/// nothing is there, or the law accepts a copy it could read and measure. Every path that changes
/// the law asks this, so a copy the law no longer accepts never waits for the next boot
/// (PRD_HELD_IGNITION §3.4). It fails closed (codex, #970): `held: false` rejects whatever is
/// there without reading it, and a copy that can't be read is `unknown`, which meets no floor.
pub fn release_under(policy: Option<&IgnitionPolicy>, hub_dir: &Path) -> Option<IgnitionRelease> {
    let path = ignition_path(hub_dir);
    if !IgnitionPolicy::held(policy) {
        return match std::fs::symlink_metadata(&path) {
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => None,
            _ => Some(IgnitionRelease::LawOff),
        };
    }
    let tier = match std::fs::read(&path) {
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return None,
        Err(_) => IgnitionTier::Unknown,
        Ok(sealed) => tier_of_sealed(&sealed),
    };
    (!tier.meets(IgnitionPolicy::min_tier(policy))).then_some(IgnitionRelease::BelowMinTier)
}

/// Whether the ledger says a copy is held: its last `IgnitionHeld` / `IgnitionReleased` is a hold.
/// This is the durable half of held ignition's state: a release is witnessed only while this is
/// true, so it is never witnessed twice, and a hold with no file on disk is a release the hub
/// still owes the ledger ([`IgnitionRelease::Absent`]).
pub fn ledger_holds<'a>(events: impl DoubleEndedIterator<Item = &'a crate::events::HubEvent>) -> bool {
    use crate::events::HubEvent;
    events
        .rev()
        .find_map(|e| match e {
            HubEvent::IgnitionHeld { .. } => Some(true),
            HubEvent::IgnitionReleased { .. } => Some(false),
            _ => None,
        })
        .unwrap_or(false)
}

/// Seals and opens the held passphrase. Production uses [`SystemdUserSealer`].
pub trait Sealer: Send + Sync {
    /// Seal `secret` into `out`, replacing it. The secret never reaches argv or the environment.
    fn seal(&self, secret: &str, out: &Path) -> Result<()>;
    /// Open the sealed file at `path`.
    fn open(&self, path: &Path) -> Result<Zeroizing<String>>;
}

/// `systemd-creds --user`: no root needed, sealed with the host key and the TPM when systemd
/// finds one.
pub struct SystemdUserSealer {
    /// `systemd-creds`, found on PATH. Tests point it at a stand-in to drive the failure arms.
    program: PathBuf,
}

impl Default for SystemdUserSealer {
    fn default() -> Self {
        Self { program: PathBuf::from("systemd-creds") }
    }
}

impl Sealer for SystemdUserSealer {
    fn seal(&self, secret: &str, out: &Path) -> Result<()> {
        let tmp = out.with_extension("cred.tmp");
        let mut child = Command::new(&self.program)
            .args(["encrypt", "--user", "--with-key=auto"])
            .arg(format!("--name={SEAL_NAME}"))
            .arg("-")
            .arg(&tmp)
            .stdin(Stdio::piped())
            .stdout(Stdio::null())
            .stderr(Stdio::piped())
            .spawn()
            .context("running systemd-creds (no sealing backend on this host?)")?;
        // Write, then always reap the child: a failed write must not leave it running or the
        // temp file behind (supervisor, #968). The stdin handle drops at the end of the
        // statement, so systemd-creds sees EOF before the wait.
        let wrote = match child.stdin.take() {
            Some(mut stdin) => stdin.write_all(secret.as_bytes()).map_err(anyhow::Error::from),
            None => Err(anyhow!("systemd-creds stdin unavailable")),
        };
        let done = child.wait_with_output()?;
        if let Err(e) = wrote {
            let _ = std::fs::remove_file(&tmp);
            return Err(e.context("passing the passphrase to systemd-creds"));
        }
        if !done.status.success() {
            let _ = std::fs::remove_file(&tmp);
            bail!("systemd-creds encrypt failed: {}", String::from_utf8_lossy(&done.stderr).trim());
        }
        // Owner-only, like the vault beside it, whatever the umask (pub, #969). Then place it.
        // Either step failing removes the temp file too (codex, #968): no failure leaves one.
        let placed = (|| -> Result<()> {
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                std::fs::set_permissions(&tmp, std::fs::Permissions::from_mode(0o600))
                    .context("restricting the sealed passphrase to its owner")?;
            }
            std::fs::rename(&tmp, out).context("placing the sealed passphrase")?;
            Ok(())
        })();
        if placed.is_err() {
            let _ = std::fs::remove_file(&tmp);
        }
        placed
    }

    fn open(&self, path: &Path) -> Result<Zeroizing<String>> {
        let done = Command::new(&self.program)
            .args(["decrypt", "--user"])
            .arg(format!("--name={SEAL_NAME}"))
            .arg(path)
            .arg("-")
            .stdin(Stdio::null())
            .output()
            .context("running systemd-creds (no sealing backend on this host?)")?;
        let out = Zeroizing::new(done.stdout);
        if !done.status.success() {
            bail!("systemd-creds decrypt failed: {}", String::from_utf8_lossy(&done.stderr).trim());
        }
        Ok(Zeroizing::new(String::from_utf8(out.to_vec()).context("sealed passphrase is not UTF-8")?))
    }
}

/// A test double that stands in for systemd. It is NOT a seal: it writes the secret in the clear
/// behind a chosen seal id. It is compiled in whenever the `test-sealer` feature is on. In this
/// workspace only the daemon's dev-dependencies turn that on, and cargo's resolver keeps dev-only
/// features out of `cargo build`, so the default release graph doesn't contain it. But anyone who
/// enables the feature explicitly compiles this clear-text implementation into their build: the
/// feature gate is not a release boundary (codex, #968). What keeps it out of a serving hub is that
/// no serving code constructs it (the census test in the daemon, I2b).
#[cfg(feature = "test-sealer")]
pub struct ClearTestSealer {
    pub seal_id: [u8; 16],
}

#[cfg(feature = "test-sealer")]
impl ClearTestSealer {
    /// A double whose seals read as `tier` (the measured id for it).
    pub fn reading_as(tier: IgnitionTier) -> Self {
        let seal_id = MEASURED_SEALS.iter().find(|(_, t)| *t == tier).map_or([0u8; 16], |(id, _)| *id);
        Self { seal_id }
    }
}

#[cfg(feature = "test-sealer")]
impl Sealer for ClearTestSealer {
    fn seal(&self, secret: &str, out: &Path) -> Result<()> {
        let mut raw = self.seal_id.to_vec();
        raw.extend_from_slice(secret.as_bytes());
        std::fs::write(out, base64::engine::general_purpose::STANDARD.encode(raw))?;
        Ok(())
    }

    fn open(&self, path: &Path) -> Result<Zeroizing<String>> {
        let raw = base64::engine::general_purpose::STANDARD.decode(std::fs::read(path)?.trim_ascii())?;
        let body = raw.get(16..).ok_or_else(|| anyhow!("sealed file too short"))?;
        Ok(Zeroizing::new(String::from_utf8(body.to_vec())?))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_law_releases_a_copy_it_no_longer_accepts() {
        let dir = tempfile::tempdir().unwrap();
        let p = |y: &str| serde_yaml::from_str::<IgnitionPolicy>(y).unwrap();
        assert_eq!(release_under(Some(&p("held: false")), dir.path()), None, "nothing held, nothing to release");
        std::fs::write(ignition_path(dir.path()), HUB_SEALED_HEAD).unwrap();
        assert_eq!(release_under(None, dir.path()), None, "the default accepts host-key");
        assert_eq!(release_under(Some(&p("held: false")), dir.path()), Some(IgnitionRelease::LawOff));
        assert_eq!(release_under(Some(&p("min_tier: tpm2")), dir.path()), Some(IgnitionRelease::BelowMinTier));
        assert_eq!(release_under(Some(&p("min_tier: host-key")), dir.path()), None);
        // codex, #970: fail closed. An unmeasured copy meets no floor, not even the lowest.
        std::fs::write(ignition_path(dir.path()), b"AAAAAAAAAAAAAAAAAAAAAAAAAAAA").unwrap();
        assert_eq!(release_under(None, dir.path()), Some(IgnitionRelease::BelowMinTier));
        assert_eq!(release_under(Some(&p("min_tier: host-key")), dir.path()), Some(IgnitionRelease::BelowMinTier));
        // A copy that can't be read is unknown too; `held: false` removes it without a read.
        std::fs::remove_file(ignition_path(dir.path())).unwrap();
        std::fs::create_dir(ignition_path(dir.path())).unwrap();
        assert_eq!(release_under(None, dir.path()), Some(IgnitionRelease::BelowMinTier));
        assert_eq!(release_under(Some(&p("held: false")), dir.path()), Some(IgnitionRelease::LawOff));
    }

    /// The first characters of the file HUB sealed on 2026-10-30 (a dummy value, not a passphrase).
    const HUB_SEALED_HEAD: &[u8] = b"VbntHThZTUOoMZ0uuzMqxiAAAAABAAAADAAAABAAAABnrmHdB+WDyarRNGcA";

    #[test]
    fn the_tier_comes_from_the_seal_id_and_an_unmeasured_id_is_unknown() {
        assert_eq!(tier_of_sealed(HUB_SEALED_HEAD), IgnitionTier::HostKey);
        let mut pub_raw = MEASURED_SEALS[1].0.to_vec();
        pub_raw.extend_from_slice(&[0x20, 0, 0, 0]);
        let pub_sealed = base64::engine::general_purpose::STANDARD.encode(pub_raw);
        assert_eq!(tier_of_sealed(pub_sealed.as_bytes()), IgnitionTier::HostTpm2);
        // A line break inside the head doesn't change the reading.
        let wrapped = [&HUB_SEALED_HEAD[..10], b"\n", &HUB_SEALED_HEAD[10..]].concat();
        assert_eq!(tier_of_sealed(&wrapped), IgnitionTier::HostKey);
        let mut other = MEASURED_SEALS[0].0;
        other[15] ^= 1;
        let other = base64::engine::general_purpose::STANDARD.encode([&other[..], &[0, 0]].concat());
        assert_eq!(tier_of_sealed(other.as_bytes()), IgnitionTier::Unknown);
        assert_eq!(tier_of_sealed(b"not base64 at all!!!!!!!!"), IgnitionTier::Unknown);
        assert_eq!(tier_of_sealed(b""), IgnitionTier::Unknown);
    }

    /// codex, #968: every way a seal can fail reaps systemd-creds and leaves neither a temp file
    /// nor a copy, and a seal that succeeds leaves exactly one owner-only copy. A stand-in script
    /// plays systemd-creds; it gets the same arguments (the temp path is the sixth).
    #[cfg(unix)]
    #[test]
    fn a_failed_seal_leaves_no_temp_file_and_a_good_one_is_owner_only() {
        use std::os::unix::fs::PermissionsExt;
        let dir = tempfile::tempdir().unwrap();
        let fake = |name: &str, body: &str| -> SystemdUserSealer {
            let p = dir.path().join(name);
            std::fs::write(&p, format!("#!/bin/sh\n{body}\n")).unwrap();
            std::fs::set_permissions(&p, std::fs::Permissions::from_mode(0o700)).unwrap();
            SystemdUserSealer { program: p }
        };
        let hub = tempfile::tempdir().unwrap();
        let out = ignition_path(hub.path());
        let tmp = out.with_extension("cred.tmp");
        let big = "x".repeat(1 << 20);
        let cases = [
            ("refuses", fake("refuses", "cat >/dev/null; echo partial > \"$6\"; echo 'no key' >&2; exit 1"), "short"),
            // Exits without reading: the write fails (a closed pipe), and the child is still reaped.
            ("stops reading", fake("stops", "echo partial > \"$6\"; exit 0"), "big"),
        ];
        for (what, sealer, secret) in cases {
            let err = sealer.seal(if secret == "big" { &big } else { "pw" }, &out).unwrap_err();
            assert!(!tmp.exists(), "{what}: the temp file is gone ({err:#})");
            assert!(!out.exists(), "{what}: nothing was placed");
        }
        let good = fake("good", "cat > \"$6\"");
        // The place is taken by a directory: the rename fails after the temp file exists.
        std::fs::create_dir(&out).unwrap();
        assert!(good.seal("pw", &out).is_err());
        assert!(!tmp.exists(), "a failed rename removes the temp file");
        std::fs::remove_dir(&out).unwrap();
        good.seal("pw", &out).unwrap();
        assert_eq!(std::fs::read_to_string(&out).unwrap(), "pw");
        assert_eq!(std::fs::metadata(&out).unwrap().permissions().mode() & 0o777, 0o600, "owner-only");
        assert!(!tmp.exists());
    }

    /// The real backend on the host running the test: seal a dummy, read its tier, open it, and
    /// check that the seal is bound to its name. Ignored by default because it needs systemd;
    /// run with `--ignored` on a host you want measured.
    #[test]
    #[ignore]
    fn the_systemd_user_sealer_round_trips_on_this_host() {
        let dir = tempfile::tempdir().unwrap();
        let path = ignition_path(dir.path());
        SystemdUserSealer::default().seal("not a passphrase", &path).unwrap();
        let tier = tier_of_sealed(&std::fs::read(&path).unwrap());
        eprintln!("this host seals at {tier:?}");
        assert_ne!(tier, IgnitionTier::Unknown, "an unmeasured seal id: add it to MEASURED_SEALS");
        assert_eq!(&*SystemdUserSealer::default().open(&path).unwrap(), "not a passphrase");
        use std::os::unix::fs::PermissionsExt;
        assert_eq!(std::fs::metadata(&path).unwrap().permissions().mode() & 0o777, 0o600, "owner-only");
        let renamed = Command::new("systemd-creds")
            .args(["decrypt", "--user", "--name=something-else"])
            .arg(&path)
            .arg("-")
            .output()
            .unwrap();
        assert!(!renamed.status.success(), "a seal must not open under another name");
    }
}
