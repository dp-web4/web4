
# Web4 Reference Demo

Run the end-to-end flow:

```bash
cd implementation/reference
python web4_demo.py
```

What it does:
- Builds toy identities and pairwise W4IDp
- Exchanges ClientHello/ServerHello
- Binds transcript via HandshakeAuth (toy COSE HMAC)
- Derives toy session keys from transcript
- Performs CreditGrant → UsageReport → Settle
- Prints a JSON bundle of the full exchange
