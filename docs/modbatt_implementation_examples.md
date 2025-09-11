# Modbatt-CAN Implementation Examples: Binding, Pairing, Witnessing, and Broadcast

*Concrete code examples from the modbatt-CAN project demonstrating the four entity relationship mechanisms*

## Overview

The modbatt-CAN project provides practical implementations of Web4's four fundamental entity relationship mechanisms. This document shows actual code examples for each mechanism.

## 1. Binding Implementation

### Binding Keys Structure
From `/mnt/c/projects/ai-agents/modbatt-CAN/WEB4 Modbatt Configuration Utility/Binding_Keys_Implementation_Plan.md`:

```cpp
typedef struct {
    uint8_t device_private_key[32];     // Never transmitted - core identity
    uint8_t device_public_key[32];      // Bound to this specific device
    uint8_t app_public_key[32];         // Upward binding link
    uint8_t module_public_key[32];      // Downward binding link
    bool keys_initialized;
} binding_keys_t;
```

### LCT Component Registration (Binding to Blockchain)
From `web4.cpp:583-625`:

```cpp
std::unique_ptr<TComponentRegistration> TWeb4BridgeClient::RegisterComponent(
    const System::UnicodeString& creator,
    const System::UnicodeString& componentData,
    const System::UnicodeString& context) {
    
    // Create permanent binding between component and LCT
    System::Json::TJSONObject* requestData = new System::Json::TJSONObject();
    TWeb4Utils::AddStringField(requestData, "creator", creator);
    TWeb4Utils::AddStringField(requestData, "component_data", componentData);
    TWeb4Utils::AddStringField(requestData, "context", context);
    
    // POST creates immutable LCT binding
    System::Json::TJSONObject* response = MakePostRequest("/api/v1/component/register", requestData);
    
    // Component now has permanent LCT identity
    std::unique_ptr<TComponentRegistration> registration(new TComponentRegistration());
    registration->FromJSON(response);
    return registration;
}
```

### Practical Binding Example
From `Unit1.cpp:3298-3301`:

```cpp
registration = FWeb4Client->RegisterComponent(
    FConfig.DefaultCreator,   // creator (blockchain account)
    componentId,              // unique hardware identifier
    componentType + "_demo"   // binding context
);
// After this, componentId is PERMANENTLY bound to its LCT
```

## 2. Pairing Implementation

### Pairing Authorization Structure
From `WEB4.h` (TPairingAuthorization class):

```cpp
class TPairingAuthorization {
    System::UnicodeString ComponentA;      // First bound entity
    System::UnicodeString ComponentB;      // Second bound entity
    System::UnicodeString OperationalContext;  // What they can do together
    System::UnicodeString AuthorizationRules;  // Constraints on relationship
};
```

### Key Halves for Pairing
From `web4.cpp:86-87`:

```cpp
// Extract cryptographic key halves for secure pairing
DeviceKeyHalf = TWeb4Utils::SafeJsonString(json->GetValue("device_key_half"));
LctKeyHalf = TWeb4Utils::SafeJsonString(json->GetValue("lct_key_half"));
```

### Creating Pairing Authorization
From `web4.cpp:1069-1101`:

```cpp
std::unique_ptr<TPairingAuthorization> TWeb4BridgeClient::CreatePairingAuthorization(
    const System::UnicodeString& componentA,
    const System::UnicodeString& componentB,
    const System::UnicodeString& operationalContext,
    const System::UnicodeString& authorizationRules) {
    
    // Request blockchain authorization for pairing
    System::Json::TJSONObject* requestData = new System::Json::TJSONObject();
    TWeb4Utils::AddStringField(requestData, "component_a", componentA);
    TWeb4Utils::AddStringField(requestData, "component_b", componentB);
    TWeb4Utils::AddStringField(requestData, "operational_context", operationalContext);
    TWeb4Utils::AddStringField(requestData, "authorization_rules", authorizationRules);
    
    // Create authorized pairing relationship
    System::Json::TJSONObject* response = MakePostRequest("/api/v1/authorization/pairing", requestData);
    
    std::unique_ptr<TPairingAuthorization> authorization(new TPairingAuthorization());
    authorization->FromJSON(response);
    return authorization;
}
```

### Initiating Pairing Process
From `web4.cpp:1304-1331`:

```cpp
std::unique_ptr<TPairingChallenge> TWeb4BridgeClient::InitiatePairing(
    const System::UnicodeString& creator,
    const System::UnicodeString& componentA,
    const System::UnicodeString& componentB,
    const System::UnicodeString& operationalContext) {
    
    // Start pairing process with challenge-response
    System::Json::TJSONObject* response = MakePostRequest("/api/v1/pairing/initiate", requestData);
    
    std::unique_ptr<TPairingChallenge> challenge(new TPairingChallenge());
    challenge->FromJSON(response);
    return challenge;  // Contains symmetric key material for paired communication
}
```

## 3. Witnessing Implementation

### Component Registration as Witnessing
From `Unit1.cpp:3298` and context:

```cpp
// App witnesses Pack Controller's existence by registering it
registration = FWeb4Client->RegisterComponent(
    FConfig.DefaultCreator,   // App is the witness
    componentId,              // Pack Controller being witnessed
    componentType + "_demo"   // Context of witnessing
);

// This creates bidirectional MRH tensor links:
// - App's tensor: "I witnessed Pack Controller"
// - Pack Controller's tensor: "App witnessed me"
```

### Trust Tensor (Witness Accumulation)
From `web4.cpp:109-151`:

```cpp
class TTrustTensor {
    System::UnicodeString ComponentA;      // Witnessing entity
    System::UnicodeString ComponentB;      // Witnessed entity
    double TrustScore;                     // Accumulated trust from witnessing
    int EvidenceCount;                     // Number of witnessing events
    double LearningRate;                   // Trust adjustment rate
    
    void FromJSON(System::Json::TJSONObject* json) {
        TrustScore = TWeb4Utils::SafeJsonNumber(json->GetValue("trust_score"), 0.5);
        EvidenceCount = static_cast<int>(TWeb4Utils::SafeJsonInt64(json->GetValue("evidence_count"), 0));
        // More witnessing = higher trust score
    }
};
```

### Witnessing Through Public Key Exchange
From the binding implementation context:

```cpp
// When Pack Controller sends its public key to App
// This is an act of mutual witnessing:
binding_keys_t pack_controller_keys;
binding_keys_t app_keys;

// Pack witnesses App
pack_controller_keys.app_public_key[32] = app_keys.device_public_key;

// App witnesses Pack
app_keys.module_public_key[32] = pack_controller_keys.device_public_key;

// Both entities now have witnessed each other's existence
```

## 4. Broadcast Implementation

### CAN Broadcast Message IDs
From `/mnt/c/projects/ai-agents/modbatt-CAN/Pack Emulator/Core/Inc/can_id_module.h:14`:

```cpp
// Module Controller to Pack Controller (Broadcast)
#define ID_MODULE_ANNOUNCEMENT     0x500  // Module broadcasts "I exist"
#define ID_MODULE_HARDWARE         0x501  // Module broadcasts capabilities
#define ID_MODULE_STATUS_1         0x502  // Module broadcasts status
```

### Sending CAN Broadcast
From `Unit1.cpp:1808-1816`:

```cpp
// Prepare broadcast message (standard CAN, not extended)
TPCANMsg CANMsg;
CANMsg.ID = StrToInt("0x"+txtID->Text);
CANMsg.LEN = (BYTE)nudLength->Position;
CANMsg.MSGTYPE = (chbExtended->Checked) ? PCAN_MESSAGE_EXTENDED : PCAN_MESSAGE_STANDARD;

// Send broadcast - no specific recipient, no encryption
if (chbRemote->Checked)
    CANMsg.MSGTYPE |= PCAN_MESSAGE_RTR;  // Remote request broadcast

// Broadcast to all devices on CAN bus
stsResult = m_objPCANBasic->Write(m_PcanHandle, &CANMsg);
```

### Module Announcement Broadcast
From context and CAN IDs:

```cpp
// Battery module broadcasts its presence
TPCANMsg broadcast;
broadcast.ID = ID_MODULE_ANNOUNCEMENT;  // 0x500 - standard broadcast ID
broadcast.MSGTYPE = PCAN_MESSAGE_STANDARD;  // Not extended (no pairing)
broadcast.LEN = 8;
broadcast.DATA[0] = MODULE_TYPE_BATTERY;
broadcast.DATA[1] = MODULE_STATE_READY;
// ... module info ...

// Send to all listeners on CAN bus
m_objPCANBasic->Write(m_PcanHandle, &broadcast);
// No acknowledgment required, no relationship formed
```

### VCU Keep-Alive Broadcast
From `Unit1.cpp:2773-2776`:

```cpp
// VCU broadcasts periodic heartbeat
CANMsg.ID = ID_VCU_KEEP_ALIVE + (packID * 0x100);
CANMsg.LEN = 8;
CANMsg.MSGTYPE = PCAN_MESSAGE_STANDARD;  // Standard broadcast

// Unidirectional announcement - "I'm still here"
// Any device can receive, no response expected
stsResult = m_objPCANBasic->Write(m_PcanHandle, &CANMsg);
```

## Complete Flow Example: All Four Mechanisms

### Step 1: Broadcast (Discovery)
```cpp
// Module broadcasts existence
broadcast.ID = ID_MODULE_ANNOUNCEMENT;
broadcast.DATA[0] = MODULE_ID;
m_objPCANBasic->Write(m_PcanHandle, &broadcast);
```

### Step 2: Witnessing (Recognition)
```cpp
// Pack Controller receives broadcast and witnesses module
// Registers module with App (creating witness chain)
FWeb4Client->RegisterComponent(
    "pack_controller",  // witness
    "module_12345",     // witnessed
    "battery_module"    // context
);
```

### Step 3: Binding (Identity)
```cpp
// If new module, create permanent LCT binding
std::unique_ptr<TComponentRegistration> registration = 
    FWeb4Client->RegisterComponent(
        creator,
        moduleId,      // Now permanently bound to LCT
        "battery_module"
    );
```

### Step 4: Pairing (Authorization)
```cpp
// Create authorized operational relationship
std::unique_ptr<TPairingAuthorization> auth = 
    FWeb4Client->CreatePairingAuthorization(
        "pack_controller_lct",
        "module_12345_lct",
        "energy_management",     // operational context
        "voltage_range:2.5-4.2"  // rules
    );

// Exchange key halves for encrypted communication
std::unique_ptr<TPairingChallenge> challenge = 
    FWeb4Client->InitiatePairing(
        creator,
        "pack_controller_lct",
        "module_12345_lct",
        "energy_management"
    );
```

## Key Implementation Insights

### 1. Separation of Concerns
- **Binding**: Hardware identity (device keys in flash)
- **Pairing**: Operational permissions (symmetric keys in RAM)
- **Witnessing**: Trust building (public key storage)
- **Broadcast**: Discovery (no keys required)

### 2. Security Boundaries
- **Binding keys**: Never leave device (private key in flash)
- **Pairing keys**: Session-based, can be rotated
- **Witness keys**: Public, shared freely
- **Broadcast**: No security, purely informational

### 3. Failure Modes
- **Binding failure**: Component has no identity (reject)
- **Pairing failure**: No permission to operate (deny)
- **Witnessing failure**: No trust established (ignore)
- **Broadcast failure**: Not discovered (timeout)

### 4. Recovery Patterns
- **Binding**: Cannot recover - new binding = new identity
- **Pairing**: Revoke and re-pair with new keys
- **Witnessing**: Re-witness to rebuild trust
- **Broadcast**: Simply broadcast again

## Conclusion

The modbatt-CAN implementation demonstrates that these four mechanisms are not just theoretical concepts but practical patterns for building secure, trustworthy IoT systems. Each mechanism serves a specific purpose:

- **Binding** provides unforgeable hardware identity
- **Pairing** enables secure operational communication
- **Witnessing** builds trust through observation
- **Broadcast** enables discovery without commitment

Together, they create a complete trust architecture from blockchain to CAN bus, implementing Web4's vision of witnessed presence and unforgeable entity relationships in real hardware.

*"In the modbatt-CAN system, every battery module broadcasts to be discovered, binds to establish identity, witnesses to build trust, and pairs to exchange energy."*