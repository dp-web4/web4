//! Held ignition's seal (hub/docs/PRD_HELD_IGNITION.md §3.2): a copy of the vault passphrase,
//! sealed by `systemd-creds --user` so it opens only on this host for this user, and read back by
//! the hub at boot.
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

use crate::law::IgnitionTier;

/// The sealed passphrase, in the hub directory.
pub const IGNITION_FILE: &str = "ignition.cred";
/// The name the seal is bound to: a file renamed to seal something else won't open as this.
const SEAL_NAME: &str = "hub-ignition";

/// Seal ids measured on real hosts (systemd 259; the ids are constants in systemd's
/// `src/shared/creds-util.h`). Only measured ids are here: any other id is
/// [`IgnitionTier::Unknown`], which ranks below every `min_tier`, so it is never held.
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

/// Seals and opens the held passphrase. Production uses [`SystemdUserSealer`].
pub trait Sealer: Send + Sync {
    /// Seal `secret` into `out`, replacing it. The secret never reaches argv or the environment.
    fn seal(&self, secret: &str, out: &Path) -> Result<()>;
    /// Open the sealed file at `path`.
    fn open(&self, path: &Path) -> Result<Zeroizing<String>>;
}

/// `systemd-creds --user`: no root needed, sealed with the host key and the TPM when systemd
/// finds one.
pub struct SystemdUserSealer;

impl Sealer for SystemdUserSealer {
    fn seal(&self, secret: &str, out: &Path) -> Result<()> {
        let tmp = out.with_extension("cred.tmp");
        let mut child = Command::new("systemd-creds")
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
        std::fs::rename(&tmp, out).context("placing the sealed passphrase")?;
        Ok(())
    }

    fn open(&self, path: &Path) -> Result<Zeroizing<String>> {
        let done = Command::new("systemd-creds")
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
/// behind a chosen seal id. Built only with the `test-sealer` feature, which only the daemon's
/// dev-dependencies turn on.
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

    /// The real backend on the host running the test: seal a dummy, read its tier, open it, and
    /// check that the seal is bound to its name. Ignored by default because it needs systemd;
    /// run with `--ignored` on a host you want measured.
    #[test]
    #[ignore]
    fn the_systemd_user_sealer_round_trips_on_this_host() {
        let dir = tempfile::tempdir().unwrap();
        let path = ignition_path(dir.path());
        SystemdUserSealer.seal("not a passphrase", &path).unwrap();
        let tier = tier_of_sealed(&std::fs::read(&path).unwrap());
        eprintln!("this host seals at {tier:?}");
        assert_ne!(tier, IgnitionTier::Unknown, "an unmeasured seal id: add it to MEASURED_SEALS");
        assert_eq!(&*SystemdUserSealer.open(&path).unwrap(), "not a passphrase");
        let renamed = Command::new("systemd-creds")
            .args(["decrypt", "--user", "--name=something-else"])
            .arg(&path)
            .arg("-")
            .output()
            .unwrap();
        assert!(!renamed.status.success(), "a seal must not open under another name");
    }
}
