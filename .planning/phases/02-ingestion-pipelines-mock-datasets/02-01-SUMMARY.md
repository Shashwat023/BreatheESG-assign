---
phase: 2
plan: "02-01"
status: complete
completed: 2026-05-25
---

# Summary: 02-01 Mock Datasets & Seed Data

## What was built

Created 3 realistic mock datasets and a seed command:

- `data/mock_datasets/sap_fuel_export.csv`: 35 rows of SAP data with mixed dates, missing values, empty rows, and multiple plant codes. Simulates the messy reality of enterprise data.
- `data/mock_datasets/utility_electricity.csv`: 24 rows of utility data covering two meters over a year, with a mix of kWh and MWh units.
- `data/mock_datasets/corporate_travel.json`: 25 records of travel data across 3 types (flight, hotel, ground_transport) with some missing flight distances.
- `data/emission_factors/factors.json`: Seed data containing DEFRA 2023 emission factors for the relevant categories.
- `apps/organizations/management/commands/seed_data.py`: A Django management command that loads the emission factors, unit conversions, and sample organizations.

## Key files created

- `data/mock_datasets/sap_fuel_export.csv`
- `data/mock_datasets/utility_electricity.csv`
- `data/mock_datasets/corporate_travel.json`
- `data/emission_factors/factors.json`
- `apps/organizations/management/commands/seed_data.py`

## Deviations from plan

None. All datasets match the acceptance criteria and the seed command is idempotent.
