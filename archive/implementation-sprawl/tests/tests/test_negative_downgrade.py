"""
test_negative_downgrade.py
Validates that suite negotiation includes proposals in transcript hash (pseudo-test).
"""
def include_in_transcript(client_proposals, server_choice):
    # Toy rule: valid if server_choice is within proposals and proposals list is hashed.
    return server_choice in client_proposals and len(client_proposals) >= 1

def test_downgrade_detected_when_choice_not_offered():
    proposals = ["W4-BASE-1","W4-FIPS-1"]
    server_choice = "W4-LEGACY-0"  # not offered
    assert not include_in_transcript(proposals, server_choice)

def test_no_downgrade_when_choice_is_offered():
    proposals = ["W4-BASE-1","W4-FIPS-1"]
    server_choice = "W4-BASE-1"
    assert include_in_transcript(proposals, server_choice)
