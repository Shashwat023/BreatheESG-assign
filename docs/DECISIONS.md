# Engineering Decisions

This document details the engineering judgments and assumptions made while building the breatheESG platform.

## 1. Architecture: Service Layer over Fat Models
**Decision:** Business logic (ingestion parsing, normalisation, audit logging) was deliberately extracted into pure Python classes in a `services/` directory rather than attaching it to Django Models or Views.
**Reasoning:** ESG data ingestion is complex. A single SAP CSV might require date parsing, unit conversion, and fallback logic. If we put this in `RawRecord.save()` (Fat Model) or `UploadViewSet.create()` (Fat View), the code becomes untestable and tightly coupled to the HTTP request lifecycle. The Service Layer pattern allows us to test the `SAPIngestionService` using pure dictionaries, entirely isolated from the database.

## 2. Ingestion Format: CSV vs API
**Decision:** SAP and Utility data is ingested via CSV upload, while Corporate Travel data is mocked as a JSON payload.
**Reasoning:**
- **SAP / Utilities:** Real-world enterprise ERPs (like SAP ECC or S/4HANA) often sit behind strict firewalls where direct API integration is politically or technically impossible. The industry standard for ESG data extraction is scheduling a monthly ABAP report that dumps a flat CSV to an SFTP server or email. Therefore, handling messy CSVs is the most realistic engineering challenge.
- **Corporate Travel:** Travel management tools like Navan (TripActions) or SAP Concur have modern, accessible REST APIs. Ingesting this data as JSON arrays closely mirrors how we would consume a webhook or API response from these platforms.

## 3. Handling Validation Failures
**Decision:** The platform ingests *all* rows from a CSV into the `RawRecord` table, even if they are fundamentally broken (e.g., missing quantities, malformed dates). The `NormalizationEngine` later flags them as `validation_status='failed'`.
**Reasoning:** If an analyst uploads a 10,000-row SAP export and 5 rows have typos, rejecting the entire upload (or silently dropping the 5 rows) is a terrible user experience. Storing everything ensures the analyst can see exactly which 5 rows failed and why, ask the originator to fix them, and continue processing the 9,995 good rows.

## 4. Normalization Engine Extraction
**Decision:** Instead of building a complex, generic "column mapping schema" builder in the UI, the extraction logic is hardcoded into Python `Strategy` classes (e.g., `SAPStrategy`).
**Reasoning:** While a UI-driven column mapper looks good in demos, enterprise ESG data is rarely clean enough for 1:1 mapping. You often need conditional logic (e.g., "If column A is empty, look at column B, and if the unit is missing, assume it is liters because this is the UK plant"). Pure Python code handles edge cases significantly better than a generic JSON-based mapping schema.

## 5. Statistical Anomaly Detection
**Decision:** To flag suspicious rows, the `ValidationService` calculates the Mean and Standard Deviation of CO2e for the batch, flagging anything >3 Sigma.
**Reasoning:** Standard Deviation is computationally cheap (PostgreSQL has built-in `StdDev` aggregate functions) and highly effective for finding fat-finger errors (e.g., typing 100000 instead of 100.00). It avoids the massive infrastructure overhead of deploying a Machine Learning model for anomaly detection.

## Questions for a Product Manager (PM)
If this were a real project kicking off, I would ask the PM:
1. **Approval Workflows:** Does an analyst's approval instantly lock the record, or does it require a secondary manager sign-off (maker-checker)?
2. **Data Correction:** If a row is flagged as suspicious, should the analyst be allowed to manually edit the quantity in the UI, or must they force the client to re-upload a corrected CSV? (Currently, we assume read-only).
3. **Emission Factor Granularity:** Do clients require custom, tenant-specific emission factors (e.g., a specific supplier's green tariff), or can we force everyone to use global DEFRA/EPA factors?
