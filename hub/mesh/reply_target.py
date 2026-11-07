"""Transport-neutral, evidence-bounded reply addressing for Hub notices.

A notice MUST be verified by the Hub channel/envelope layer before calling
select_reply_target. This module only interprets already-authenticated fields;
it does not authenticate either identity or confer permission to send.

Transferred from private-context #82 toward Web4 #982. Not wired into the
fleet sender yet: the public Hub is the authoritative implementation target.
"""

from dataclasses import dataclass
import re
from typing import Mapping, Any


# Current key-derived canonical Web4 presence ids; aliases are not presence.
_CANONICAL_LCT = re.compile(r"lct:web4:mb32:b[a-z2-7]{52}")


class InvalidNoticeAddress(ValueError):
    """Refuse missing, contradictory or unresolvable address metadata."""


@dataclass(frozen=True)
class ReplyTarget:
    kind: str  # "canonical_lct" or "hub_member"
    identifier: str


def select_reply_target(verified_notice: Mapping[str, Any]) -> ReplyTarget:
    """Choose the *authored* target, not necessarily the transport router.

    The caller is responsible for verifying the Hub notice and ensuring that
    `from_lct` was covered by its authenticated provenance. Reject malformed
    authored identities rather than silently falling back to the router.
    Delivery/polling eligibility must be checked by the Hub before sending.
    """
    router = verified_notice.get("from")
    if not isinstance(router, str) or not router.strip() or router != router.strip():
        raise InvalidNoticeAddress("missing or malformed transport sender")

    if "from_lct" not in verified_notice:
        return ReplyTarget(kind="hub_member", identifier=router)

    authored = verified_notice["from_lct"]
    if not isinstance(authored, str) or not _CANONICAL_LCT.fullmatch(authored):
        raise InvalidNoticeAddress("malformed canonical author; no router fallback")
    return ReplyTarget(kind="canonical_lct", identifier=authored)
