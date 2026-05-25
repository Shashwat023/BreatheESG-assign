# Tradeoffs & Omitted Features

To deliver a high-quality, stable prototype within the constraints of the assignment, several features were intentionally omitted. Documentation of these tradeoffs demonstrates an understanding of production scale vs. prototype scope.

## 1. Asynchronous Distributed Ingestion (Celery/RabbitMQ)
**Omitted:** The current `IngestionService` processes CSV rows synchronously within the HTTP request/response cycle.
**Why omitted:** Setting up Celery, Redis/RabbitMQ, and managing background workers adds massive deployment complexity. For CSVs under 10,000 rows, a well-optimized Python script can process them synchronously in a few seconds. 
**How it would be added later:** 
1. The `RawUpload` record is created synchronously.
2. The HTTP response immediately returns `{"status": "processing", "upload_id": 1}`.
3. A Celery task `@shared_task def process_csv(upload_id)` is dispatched to a background worker to handle the row-by-row insertion.
4. The React frontend uses WebSockets or long-polling to listen for progress updates.

## 2. OCR / PDF Parsing for Utility Bills
**Omitted:** The utility ingestion service only accepts structured CSVs, not raw PDF invoices.
**Why omitted:** Extracting reliable structured data from heterogeneous PDF layouts requires specialized tools (e.g., AWS Textract, Google Document AI) and significant validation logic. Building a brittle regex-based PDF parser for a prototype creates technical debt.
**How it would be added later:** We would integrate a third-party OCR API. The upload endpoint would accept the PDF, send it to Document AI, map the extracted text blocks (Total kWh, Billing Period) into a JSON dictionary, and then pass that dictionary to the exact same `UtilityIngestionService` we built for the CSVs.

## 3. Machine Learning Anomaly Detection
**Omitted:** Suspicious rows are currently flagged using simple statistical bounds (Mean + 3 Standard Deviations) rather than an ML Isolation Forest or Neural Network.
**Why omitted:** ML models require massive amounts of historical, labeled training data to be accurate, which we don't have. Furthermore, deploying ML models requires specialized infrastructure (GPU instances, separate microservices). 
**How it would be added later:** Once we have millions of rows of analyst-reviewed data (where analysts have marked rows as `rejected` due to errors), we could export this dataset to train an Isolation Forest model in scikit-learn. The model would be served via a lightweight FastAPI microservice that the Django backend queries during the normalization phase.

## 4. Advanced Role-Based Access Control (RBAC)
**Omitted:** The platform currently assumes any user can view and approve any record.
**Why omitted:** Implementing Django Guardian for row-level permissions or complex Group architectures distracts from the core engineering challenge (ingestion and normalization).
**How it would be added later:** We would introduce an `AnalystRole` and `ClientRole`. Clients can only `POST` uploads. Analysts can `GET` records and `POST` approvals. We would enforce this using Django REST Framework's `BasePermission` classes.
