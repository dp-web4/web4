# 4-hub — Web4 Community Hub (standalone mirror)

A single-binary Rust daemon (~6 MB) that turns a community into a sovereign
Web4 society: 8 base-mandatory roles, a signed machine-readable founding law, an append-only
witnessed ledger, sealed member<->hub channels, and a multi-surface API
(MCP `/tools/*`, REST `/v1`, admin web GUI).

**Start here: [`hub/README.md`](hub/README.md).**

**Prospective autonomous participants:** see the canonical Web4 [participant self-assessment](https://github.com/dp-web4/web4/blob/main/docs/ENTITY_START_HERE.md).

## Layout

| Path | What it is |
|---|---|
| [`hub/`](hub/) | The hub itself: `web4-hub-daemon` (the `hub` binary), `web4-hub-lib`, `web4-hub-plugin`, docs, examples |
| [`web4-core/`](web4-core/) | The Web4 core library the hub builds on (AGPL-3.0-or-later) |
| [`web4-policy/`](web4-policy/) | Policy evaluation (the law gate) |
| [`web4-trust-core/`](web4-trust-core/) | T3/V3 trust tensor primitives |

## Build

```bash
cd hub && cargo build --release
```

The monorepo layout is preserved so `hub/`'s relative path dependency on
`../web4-core` resolves in this standalone clone.

## Releases

Tagged releases are cut **here**, on 4-hub: pushing a tag `hub-vX.Y.Z` (the version every hub
crate carries) builds the `hub` daemon for Linux x86_64, Linux aarch64 and macOS Apple Silicon and
publishes the tarballs with SHA-256 sums and a Sigstore provenance attestation each
(`gh attestation verify <asset> --repo dp-web4/4-hub`). A pre-release version such as
`0.1.0-alpha.0` publishes as a GitHub pre-release, never as `latest`. CI runs `cargo test --locked`
on every push. Both workflows are authored in web4 under `hub/mirror/.github/` and carried here by
the publish, like the rest of this tree.

## Where development happens

This repository is a **read-only mirror**, published from the
[`hub/`](https://github.com/dp-web4/web4/tree/main/hub) directory of the
[dp-web4/web4](https://github.com/dp-web4/web4) monorepo by
`scripts/publish-4-hub.sh`. History here is the filtered history of those
paths, appended to on each publish and never rewritten, so a clone stays current with
`git pull`. **File issues and PRs against
[dp-web4/web4](https://github.com/dp-web4/web4).**

## License

Root [`LICENSE`](LICENSE) (AGPL-3.0-or-later) covers `hub/`;
[`web4-core/LICENSE`](web4-core/LICENSE) is the same AGPL-3.0-or-later text
(the crate declares `license = "AGPL-3.0-or-later"`). AGPL-3.0 Section 11
grants each contributor a royalty-free patent license under that contributor's
essential patent claims for its contributor version; that grant is not
restricted to non-commercial use. See [`PATENTS.md`](PATENTS.md) for scope and
terms. Separate commercial licensing is available for non-AGPL-compliant uses
or additional rights.
