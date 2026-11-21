# Delaware AIC Rulebook (example) — operator interview

generated 2026-11-19 · 3 open of 3. 
answer in any form (a word is fine). each answer gets recorded with `python3 rulebook.py answer <id> "..."` and the rows it touches are confirmed, amended, or retired.

### q-01 · Does a hub ledger entry signed with the manager's key satisfy 'signed record' (§81-102(26): 'with present intent to authenticate or adopt')? Can software have present intent?

why: The statute's evidence is the agent's own signature; whether that counts is a question for the drafter.  
draft rule r-02: _The manager must document every action it takes in a signed record._  
likely answers: yes, as an electronic process / needs a member's adoption / unclear

### q-02 · Is a self-signed log enough for the administrator, or should the record be witnessed by something the agent doesn't control?

why: A record only the agent signed is self-attestation; Oversight's transparency concern points here.  
draft rule r-05: _The AIC's records relevant to the sandbox must be available for audit by the Sandbox Administrator on request._  
likely answers: self-signed is enough / independent witness required / committee rule

### q-03 · What counts as 'promptly cease' (§8005(c)(6)c.1): seconds, hours? Must it reach every execution path?

why: The demo stops the gated paths at once; ungated paths are out of scope (A1).  
draft rule r-07: _On suspension or revocation, every act of the AI agents must stop, except wind-down acts._  
likely answers: immediately / within a day / committee rule
