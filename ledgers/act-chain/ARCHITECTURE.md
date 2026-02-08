# ACT Chain Architecture

Technical documentation of the ACT distributed ledger implementation.

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Cosmos SDK | v0.53.x | Modular blockchain framework |
| CometBFT | v0.38.x | Byzantine consensus |
| Go | 1.24+ | Implementation language |
| Protobuf | v1.36+ | Message serialization |

## Module Overview

### lctmanager

**Purpose**: Linked Context Token identity management

**Messages**:
- `MsgCreateLCT` - Mint new LCT
- `MsgBindLCT` - Bind LCT to hardware
- `MsgRevokeLCT` - Revoke identity
- `MsgDelegateLCT` - Create delegation

**Queries**:
- `QueryLCT` - Get LCT details
- `QueryLCTsByOwner` - List LCTs for owner
- `QueryLCTHistory` - Get LCT history

**State**:
```protobuf
message LinkedContextToken {
  string lct_id = 1;
  bytes ed25519_public_key = 2;
  bytes x25519_public_key = 3;
  bytes binding_signature = 4;
  string did = 5;
  string owner = 6;
  int64 created_at = 7;
}
```

### energycycle

**Purpose**: ATP/ADP energy economy

**Messages**:
- `MsgDischargeATP` - Convert ATP to ADP (spend energy)
- `MsgRechargeADP` - Convert ADP to ATP (earn energy)
- `MsgTransferATP` - Transfer ATP between entities
- `MsgSlashATP` - Penalty mechanism

**Queries**:
- `QueryBalance` - Get ATP/ADP balance
- `QueryTransactionHistory` - Get transaction log
- `QuerySocietyPool` - Get federation pool status

**State**:
```protobuf
message EnergyAccount {
  string lct_id = 1;
  int64 atp_balance = 2;
  int64 adp_balance = 3;
  int64 initial_allocation = 4;
  int64 daily_recharge = 5;
  string last_recharge = 6;
}

message EnergyOperation {
  string operation_id = 1;
  string type = 2;  // discharge, recharge, transfer, slash
  string from_lct = 3;
  string to_lct = 4;
  int64 amount = 5;
  string reason = 6;
  string timestamp = 7;
  repeated string witness_signatures = 8;
}
```

### trusttensor

**Purpose**: T3/V3 multi-dimensional trust

**Messages**:
- `MsgUpdateTrust` - Update T3 scores
- `MsgRecordWitness` - Record witnessing event
- `MsgDecayTrust` - Apply temporal decay

**Queries**:
- `QueryTrustTensor` - Get T3/V3 for entity
- `QueryTrustHistory` - Historical tensor values
- `QueryWitnessChain` - Get witness relationships

**State**:
```protobuf
message TrustTensor {
  string lct_id = 1;
  string role = 2;

  // T3 dimensions
  double talent = 3;      // Natural aptitude
  double training = 4;    // Learned skills
  double temperament = 5; // Consistency

  // V3 dimensions
  double valuation = 6;   // Economic worth
  double veracity = 7;    // Truthfulness
  double validity = 8;    // Current relevance

  repeated double context_weights = 9;
  string last_updated = 10;
}
```

### mrh

**Purpose**: Markov Relevancy Horizon context boundaries

**Messages**:
- `MsgCreateMRH` - Create context boundary
- `MsgLinkMRH` - Link entities to MRH
- `MsgUpdateMRH` - Update relevancy scores

**Queries**:
- `QueryMRH` - Get MRH details
- `QueryEntitiesInMRH` - List entities in boundary
- `QueryMRHOverlap` - Check overlap between MRHs

**State**:
```protobuf
message MarkovRelevancyHorizon {
  string mrh_id = 1;
  string owner_lct = 2;
  repeated string linked_entities = 3;
  map<string, double> relevancy_scores = 4;
  string created_at = 5;
}
```

### pairing

**Purpose**: Device authentication and session keys

**Messages**:
- `MsgInitiatePairing` - Start pairing flow
- `MsgCompletePairing` - Finish pairing
- `MsgExchangeSessionKey` - Establish session

**State**:
```protobuf
message PairingRecord {
  string pairing_id = 1;
  string initiator_lct = 2;
  string responder_lct = 3;
  bytes shared_secret_hash = 4;
  string status = 5;  // pending, active, revoked
  string created_at = 6;
}
```

### componentregistry

**Purpose**: Physical component tracking

**Messages**:
- `MsgRegisterComponent` - Register hardware
- `MsgBindComponent` - Bind to LCT
- `MsgUpdateComponent` - Update status

**State**:
```protobuf
message Component {
  string component_id = 1;
  string type = 2;  // battery, controller, sensor
  string bound_lct = 3;
  map<string, string> metadata = 4;
  string status = 5;
}
```

### societytodo

**Purpose**: Society-level task delegation

**Messages**:
- `MsgCreateTask` - Create delegated task
- `MsgClaimTask` - Claim for execution
- `MsgCompleteTask` - Mark complete
- `MsgVerifyTask` - Verify completion

**State**:
```protobuf
message SocietyTask {
  string task_id = 1;
  string creator_lct = 2;
  string assignee_lct = 3;
  string description = 4;
  int64 atp_reward = 5;
  string status = 6;  // open, claimed, completed, verified
  repeated string verifier_signatures = 7;
}
```

## Consensus Configuration

```toml
# CometBFT configuration
[consensus]
timeout_propose = "3s"
timeout_prevote = "1s"
timeout_precommit = "1s"
timeout_commit = "5s"

# Block parameters
max_block_size_bytes = 22020096
max_gas = -1
time_iota_ms = 1000
```

## Genesis Configuration

```json
{
  "chain_id": "act-web4",
  "initial_height": 1,
  "app_state": {
    "energycycle": {
      "federation_pool": {
        "total_atp": 100000,
        "emergency_reserve": 5000,
        "daily_recharge_rate": 10000
      }
    },
    "lctmanager": {
      "genesis_entities": [
        {"name": "Genesis Queen", "atp": 30000},
        {"name": "Genesis Council", "atp": 20000}
      ]
    }
  }
}
```

## Transaction Flow

```
1. Client creates transaction
         ↓
2. Signs with Ed25519 key
         ↓
3. Adds witness attestations
         ↓
4. Encodes as base64
         ↓
5. Submits to RPC (broadcast_tx_commit)
         ↓
6. CometBFT proposes block
         ↓
7. Validators reach consensus
         ↓
8. Block committed
         ↓
9. State updated
```

## Key Algorithms

### ATP Discharge

```go
func (k Keeper) DischargeATP(ctx sdk.Context, from string, amount int64, reason string) error {
    account := k.GetAccount(ctx, from)

    if account.AtpBalance < amount {
        return ErrInsufficientATP
    }

    account.AtpBalance -= amount
    account.AdpBalance += amount

    k.SetAccount(ctx, account)
    k.EmitEvent(ctx, "atp_discharged", from, amount, reason)

    return nil
}
```

### Trust Update

```go
func (k Keeper) UpdateTrust(ctx sdk.Context, lct string, outcome Outcome) {
    tensor := k.GetTrustTensor(ctx, lct)

    // Apply outcome-based delta
    delta := calculateDelta(outcome)

    tensor.Talent = clamp(tensor.Talent + delta.Talent, 0, 1)
    tensor.Training = clamp(tensor.Training + delta.Training, 0, 1)
    tensor.Temperament = clamp(tensor.Temperament + delta.Temperament, 0, 1)

    tensor.LastUpdated = ctx.BlockTime().String()
    k.SetTrustTensor(ctx, tensor)
}
```

## API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/act/lct/{id}` | Get LCT details |
| GET | `/act/energy/{lct}` | Get ATP/ADP balance |
| GET | `/act/trust/{lct}` | Get trust tensor |
| POST | `/act/tx` | Submit transaction |

### gRPC Services

```protobuf
service Query {
  rpc LCT(QueryLCTRequest) returns (QueryLCTResponse);
  rpc Balance(QueryBalanceRequest) returns (QueryBalanceResponse);
  rpc TrustTensor(QueryTrustRequest) returns (QueryTrustResponse);
}

service Msg {
  rpc CreateLCT(MsgCreateLCT) returns (MsgCreateLCTResponse);
  rpc DischargeATP(MsgDischargeATP) returns (MsgDischargeATPResponse);
  rpc UpdateTrust(MsgUpdateTrust) returns (MsgUpdateTrustResponse);
}
```

## See Also

- [README.md](README.md) - Overview and quick start
- [spec/](spec/) - Module specifications
- [bridge/](bridge/) - Python integration
- [../../spec/fractal-chains/root-chains.md](../../spec/fractal-chains/root-chains.md) - Root chain role
