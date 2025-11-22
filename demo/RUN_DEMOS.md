# Running the Web4 Demos

This guide shows how to run the **Store Demo** (merchant) and the **Delegation Manager UI** together, and how to exercise the trust and approval flows.

## 1. Prerequisites

- Python 3.10+ installed and on PATH.
- `pip` available for installing dependencies.
- (Recommended) A virtual environment for this repo.

From the repo root:

```bash
cd demo/store
pip install -r requirements.txt

cd ../delegation-ui
pip install -r requirements.txt
```

> If `cryptography` prints messages about Rust, it is trying to compile from source. On most Windows setups the prebuilt wheels will be used; if not, installing Rust from https://rustup.rs may be required.

---

## 2. Start the Delegation Manager UI

From the repo root:

```bash
cd demo/delegation-ui
python app.py
```

Then open:

- http://localhost:8001

What you can do here:

- **Create delegations** for agents (e.g. `agent-claude-demo`).
- Set spending limits and allowed resources.
- See **pending approvals** for high-value purchases.
- View **activity** and **T3 trust scores** for agents.

---

## 3. Start the Store Demo (Merchant)

In a second terminal, from the repo root:

```bash
cd demo/store
python app.py
```

Then open:

- Store home: http://localhost:8000
- Store dashboard: http://localhost:8000/dashboard

The store exposes a simple product catalog with an "🤖 Agent Purchase" button for each item. Purchases are executed by a demo agent (`agent-claude-demo`) using the Web4 authorization stack.

---

## 4. Walkthrough: Trust and Approvals in Action

### Step 1 – Create a delegation

1. Go to **Delegation Manager**: http://localhost:8001
2. On the **Create Delegation** tab:
   - Set **Agent Name** to something like `Claude (demo)`.
   - Set **Agent ID** to `agent-claude-demo`.
   - Leave budgets at defaults or adjust as you like.
   - Choose allowed resources (e.g. books and music).
   - Click **Create Delegation**.
3. Switch to **Manage Delegations** to see the new entry and its T3 trust section.

### Step 2 – Normal purchases and trust evolution

1. Go to the **Store**: http://localhost:8000
2. Click **🤖 Agent Purchase** on lower-priced items (e.g. books/music under $75).
3. After a successful purchase, visit the **Store Dashboard**:
   - http://localhost:8000/dashboard
4. Observe:
   - **Daily Budget** usage.
   - **ATP Budget**.
   - **Agent Trust (T3)**: talent, training, temperament, composite, and transaction stats.
   - Recent purchases in **Activity**.

Each successful, in-constraint purchase updates the agent’s T3 profile via the `T3Tracker`.

### Step 3 – Low-trust, high-value gate

The store enforces a demo-local policy:

- If **composite T3 trust < 0.30** and
- The product price is **≥ $75.00**,
- Then the purchase is denied and routed to the Delegation Manager for approval.

To see this:

1. From the **Store**, attempt to buy a high-priced item (e.g. `Introduction to Machine Learning`).
2. If the agent’s trust is still low, you will see a message like:

   > Agent trust too low for high-value purchase. Trust X.XX < 0.30 for items over $75.00. Approval request created. Open the Delegation Manager to review (ID: app-...).

3. Go to **Delegation Manager → Pending Approvals**:
   - http://localhost:8001
   - You should see a card for the high-value purchase request.
4. Approve or deny the request.
5. Check **Activity** to see the approval response logged.

At this point you have:

- Verified end-to-end Web4 authorization for normal purchases.
- Seen **T3 trust** update based on outcomes.
- Triggered a **human approval requirement** driven by low trust for high-value items.

---

## 5. Trust Visualizer Example

The trust visualizer is a separate static example that shows simplified trust dynamics over time.

From the repo root:

1. Open the file directly in a browser:

   ```
   c:\projects\ai-agents\web4\examples\trust-visualizer\index.html
   ```

2. Or serve via a simple static server (example):

   ```bash
   cd examples/trust-visualizer
   python -m http.server 8080
   # then visit http://localhost:8080/index.html
   ```

Use the **Positive / Negative / Neutral / Random** buttons to see the trust line and uncertainty band evolve.

---

This document is intentionally minimal; for deeper architectural context, see the root `README.md`, `WINDSURF_QUICKSTART.md`, and `DEMO_SCRIPT.md`.
