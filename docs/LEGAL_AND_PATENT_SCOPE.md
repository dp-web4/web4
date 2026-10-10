# Web4 licensing and patent scope — reader guide

**Status:** explanatory guidance, not a new license, additional patent grant, legal opinion, or amendment. In conflicts, actual licenses, applicable patent grants, contributor rights and law control. Reviewed against repository text on 2026-10-09.

## Read this first
- [Root LICENSE](../LICENSE): operative software license.
- [PATENTS.md](../PATENTS.md): patent inventory, Section 11 explanation, commercial contact.
- [Repository README](../README.md): project/component overview.
- Component-level license files, manifests, and notices must also be checked. Do not assume every path or historical version has identical terms.

## What is already granted
The Web4 root describes its code as **AGPL-3.0-or-later unless a subdirectory states otherwise**. Under AGPL v3 Section 11, each contributor provides a worldwide, nonexclusive, royalty-free license under that contributor's *essential patent claims* for its contributor version. This is not a ban on commercial use: AGPL-compliant commercial activity is permitted. The patent notice does not retract rights given by AGPL.

AGPL compliance matters for modifying, distributing and operating covered software over networks; consult the license for actual obligations. Do not infer an exemption simply because communication happens through a protocol boundary or the code is not directly distributed.

## Distinct situations
| Situation | Reading |
|---|---|
| Reading or discussing published Web4 specifications | Public availability permits inspection; copyright, trademarks and patents remain separate considerations. No software copying is implied. |
| Using, modifying, redistributing or operating Web4 code | Read the applicable component license and patent terms; AGPL v3 Section 11 is tied to essential claims and contributor versions, not a promise of all patent rights. |
| Implementing the protocol independently, without copying Web4 code | Do **not** assume the contributor-version Section 11 grant is a blanket standards-essential patent license. Patent exposure and any additional permission require separate analysis. |
| Integrating independent systems through a network interface | A technical bridge does not inherently merge legal obligations or grant patent rights; analyze any code transfer, combination, modifications, network-service behavior, and claims actually implicated. |
| Proprietary or separately licensed uses | Contact MetaLINXX Inc. for a separate agreement where applicable; no alternative grant is created by this page. |

## Patents versus software
The patent notice lists issued US 11,477,027 and 12,278,913 plus pending applications 19/178,619 and 19/803,885. Listing an application does not mean it is issued, nor does listing a patent demonstrate that every implementation infringes every claim. Coverage turns on claims and implementation details. An independent interoperability implementation may require more analysis than a compliant use of contributed code.

## Hub / Hestia / enterprise
- **Hub** canonical source is `web4/hub/`; the `4-hub` repository is a published mirror. The Hub README references the Web4 root license and patent terms.
- **Hestia** has its own AGPL-3.0-or-later license, plus separate commercial licensing information. Check its own files; Web4's notice is not automatically a blanket additional grant covering unrelated Hestia code.
- **Hardbound** is a separate proprietary enterprise offering. Its availability does not restrict previously granted rights in the open components.

## Known documentation discrepancy to verify
An older `mcp-server/README.md` says “MIT” while the Web4 session primer says everything is AGPL and the root README allows explicit subdirectory exceptions. The MCP directory currently contains no separate LICENSE file. **Do not silently resolve this by deleting historical MIT text or asserting that it conclusively establishes a separate license.** Inspect file headers, provenance, prior revisions and publication history; obtain rights-holder review before making a definitive determination. The ambiguous README should point here pending that audit.

## FAQ
**Can a business use Web4?** Yes, AGPL does not exclude commercial use. Whether a particular business deployment complies depends on how it uses, modifies and offers the software.

**Does Web4 promise unrestricted implementation of its standard?** Not in the documents reviewed. The contributor-version patent grant should not be advertised as an unconditional grant for all independent implementations.

**Can two sovereign agent societies bridge without merging codebases?** Technically, yes; that does not alone settle the licensing or patent status of the implementations.

**Is this a new grant?** No. This page is a map of existing documentation. No licenses, patents, trademarks, contributor terms or source-code rights have been changed.

## Future decision (not adopted)
A separate, express patent commitment for standards-conformant *independent implementations* might reduce adoption friction, but must be drafted and approved with patent counsel and the actual rights holder. Consider claim scope, conformance definition, reciprocity, termination, geographic scope, and consistency with preexisting contributor rights. Until then, do not imply such a grant exists.

**Questions / separate commercial rights:** dp@metalinxx.io.
