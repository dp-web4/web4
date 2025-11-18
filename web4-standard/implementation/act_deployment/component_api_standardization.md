# Component API Standardization

**Session #44**

## Problem

Components have inconsistent initialization APIs, causing integration failures:

1. **EnergyCapacityRegistry** (dataclass)
   - Required: `society_lct: str`
   - Usage: `EnergyCapacityRegistry(society_lct="lct-foo")`

2. **HardenedEnergyCapacityRegistry** (class with __init__, inherits from dataclass)
   - Required: `society_lct: str, global_registry: GlobalEnergyRegistry, device_spec_db: DeviceSpecDatabase`
   - Usage: `HardenedEnergyCapacityRegistry(society_lct="...", global_registry=..., device_spec_db=...)`
   - **PROBLEM**: Inherits from dataclass but uses traditional `__init__` → API confusion

3. **EnergyBackedBondRegistry** (dataclass)
   - Required: None (all fields have defaults)
   - Usage: `EnergyBackedBondRegistry()`

4. **Integration failure**:
   - `integrated_society_node.py:135` tries: `HardenedEnergyCapacityRegistry()`
   - This fails because required arguments are missing

## Solution: Factory Pattern

Standardize all components to use **factory methods** for initialization:

### Design Principle
```python
# Base class: dataclass with sensible defaults
@dataclass
class ComponentBase:
    field1: Type = default_value
    field2: Type = field(default_factory=factory)

    @classmethod
    def create(cls, **kwargs) -> "ComponentBase":
        """Factory method for clear initialization."""
        return cls(**kwargs)
```

### Benefits
1. **Consistent API**: All components use `.create()` factory method
2. **Clear requirements**: Factory method documents required vs optional args
3. **Validation**: Factory can validate args before construction
4. **Flexibility**: Can have multiple factory methods (create_default, create_hardened, etc.)
5. **Inheritance-friendly**: Dataclass inheritance works cleanly

## Implementation Plan

### Phase 1: Add factory methods to existing classes (non-breaking)
- Add `.create()` classmethod to `EnergyCapacityRegistry`
- Add `.create()` classmethod to `EnergyBackedBondRegistry`
- Convert `HardenedEnergyCapacityRegistry` to use dataclass + factory pattern

### Phase 2: Add convenience factories
- `EnergyCapacityRegistry.create_for_society(society_lct)`
- `HardenedEnergyCapacityRegistry.create_hardened(society_lct, global_registry, device_spec_db)`
- `EnergyBackedBondRegistry.create()`

### Phase 3: Update all call sites
- Update tests to use factory methods
- Update integrated node to use factory methods
- Update demos to use factory methods

### Phase 4: Document patterns
- Update component docs with factory usage
- Add migration guide for users

## Example: Standardized HardenedEnergyCapacityRegistry

### Before (broken inheritance)
```python
class HardenedEnergyCapacityRegistry(EnergyCapacityRegistry):
    def __init__(
        self,
        society_lct: str,
        global_registry: GlobalEnergyRegistry,
        device_spec_db: DeviceSpecDatabase,
    ):
        super().__init__(society_lct=society_lct)
        self.global_registry = global_registry
        self.device_spec_db = device_spec_db
```

### After (dataclass with optional fields)
```python
@dataclass
class HardenedEnergyCapacityRegistry(EnergyCapacityRegistry):
    """Hardened registry with security mitigations."""

    global_registry: Optional[GlobalEnergyRegistry] = None
    device_spec_db: Optional[DeviceSpecDatabase] = None

    @classmethod
    def create_hardened(
        cls,
        society_lct: str,
        global_registry: GlobalEnergyRegistry,
        device_spec_db: DeviceSpecDatabase,
    ) -> "HardenedEnergyCapacityRegistry":
        """Create hardened registry with all security features."""
        return cls(
            society_lct=society_lct,
            global_registry=global_registry,
            device_spec_db=device_spec_db,
        )

    @classmethod
    def create_for_testing(
        cls,
        society_lct: str,
    ) -> "HardenedEnergyCapacityRegistry":
        """Create registry for testing (no security)."""
        return cls(society_lct=society_lct)
```

### Usage
```python
# Production
registry = HardenedEnergyCapacityRegistry.create_hardened(
    society_lct="lct-foo",
    global_registry=GlobalEnergyRegistry(),
    device_spec_db=DeviceSpecDatabase(),
)

# Testing
registry = HardenedEnergyCapacityRegistry.create_for_testing("lct-foo")
```

## Migration Path

1. Add factory methods alongside existing constructors (non-breaking)
2. Update internal code to use factories
3. Update tests
4. Mark old constructors as deprecated (in docstrings)
5. Eventually remove support for direct construction (breaking change in v2.0)

## Success Criteria

- ✅ All components can be instantiated via `.create()` or specific factory
- ✅ `integrated_society_node.py` successfully initializes all components
- ✅ All existing tests pass
- ✅ New tests demonstrate factory pattern usage
- ✅ API documented in component docstrings
