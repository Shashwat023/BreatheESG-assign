# Data Sources & Ingestion Research

This document explains the research and rationale behind the three mocked data sources ingested by the platform.

## 1. SAP ERP Extracts (Fuel / Procurement)
**Format:** CSV
**File:** `data/mock_datasets/sap_fuel_export.csv`

### Research & Reality
In large enterprises, fuel usage (diesel for generators, petrol for fleet) is usually tracked in procurement systems like SAP ECC or S/4HANA. The data is notoriously messy:
- Plant codes (`Werk`) and Material codes (`Material`) are often exported with German headers.
- Date formats vary wildly depending on the Windows locale of the user who exported the CSV (e.g., `15.01.2024` vs `2024-01-15`).
- Commas are frequently used as decimal separators in Europe (`1.000,50` instead of `1000.50`).

### Ingestion Strategy
The `SAPIngestionService` implements a column mapping dictionary that translates known German and English headers into canonical keys. The `SAPStrategy` normalizer includes specific logic to strip European comma formatting and fuzzy-parse dates.

### Production Limitations
If a plant begins exporting using a completely unknown material code (e.g., `BIO-X`), the normalization engine will flag it as `Unknown Fuel`, requiring a developer to update the `FUEL_TYPE_MAP`. In production, this mapping table should be moved to the database so administrators can update it without deploying code.

---

## 2. Utility Invoices (Electricity)
**Format:** CSV
**File:** `data/mock_datasets/utility_electricity.csv`

### Research & Reality
Organizations receive hundreds of electricity bills monthly across different sites. While PDF is common, enterprise energy brokers (like Schneider Electric) or large utilities provide CSV summaries. 
- A major challenge is unit inconsistency: some meters report in `kWh`, others in `MWh`.
- Billing periods often overlap months (e.g., Jan 15 to Feb 14), complicating annual reporting.

### Ingestion Strategy
The `UtilityIngestionService` grabs the exact `Energy_Consumed` and `Unit`. The `NormalizationEngine` detects if the unit is `MWh` and uses the database `UnitConversion` table to reliably multiply it by 1000 to reach the canonical `kWh` required by the grid emission factors.

### Production Limitations
The system currently assigns the emission year based on `Billing_Period_Start`. If a bill crosses into a new calendar year (Dec 15 to Jan 15), applying the previous year's grid factor to January's energy is technically inaccurate. A production system must pro-rata the energy across the days in each year.

---

## 3. Corporate Travel (Navan / Concur)
**Format:** JSON
**File:** `data/mock_datasets/corporate_travel.json`

### Research & Reality
Modern travel management companies provide APIs that return rich JSON arrays. 
- Flight records often lack exact distances (`distance_km`) but provide origin and destination airport codes (e.g., `LHR` to `JFK`).
- The data is highly nested and contains multiple object types (Flights, Hotels, Trains) in a single stream.

### Ingestion Strategy
The `TravelIngestionService` iterates over the JSON array, verifying the `travel_type` key. The `TravelStrategy` normalizer applies fallback logic: if a flight distance is missing, it injects a placeholder estimate (in a real system, it would call an external API like the Great Circle Mapper to calculate distance via latitude/longitude). 

### Production Limitations
The hardcoded fallback distance for flights is insufficient for real accounting. In production, this requires an asynchronous geospatial microservice.
