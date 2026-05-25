---
phase: 3
plan: "03-01"
status: complete
completed: 2026-05-25
---

# Summary: 03-01 Normalization Engine

## What was built

Implemented the `NormalizationEngine` and source-specific strategies that convert verbatim `RawRecord`s into unified `NormalizedEmissionRecord`s with CO2e calculations.

- `services/normalization/strategies.py`: Implemented `SAPStrategy`, `UtilityStrategy`, and `TravelStrategy`. These extract standard fields (`activity_value`, `category`, dates) from the messy raw data JSON while isolating source-specific logic.
- `services/normalization/engine.py`: Implemented `NormalizationEngine` which:
  1. Calls the appropriate strategy to extract fields.
  2. Looks up the `EmissionFactor` using year/category fallback logic.
  3. Uses `UnitConversion` to normalize the activity unit to match the factor's expected unit.
  4. Calculates `co2e`.
  5. Implements the snapshot pattern (saving `emission_factor_value` locally).
  6. Safely handles failures by trapping exceptions and updating `RawRecord.validation_status` without crashing the batch.

## Key files created

- `services/normalization/__init__.py`
- `services/normalization/strategies.py`
- `services/normalization/engine.py`

## Deviations from plan

None. All normalization rules were implemented as specified in the service-layer architecture.
