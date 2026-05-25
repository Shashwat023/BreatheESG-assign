# breatheESG — Enterprise ESG Ingestion Platform

An enterprise-grade platform designed to ingest messy, real-world data (SAP exports, Utility bills, Travel APIs), normalize it into a unified Schema, calculate CO2e, and provide analysts with a fully traceable, immutable audit trail.

**Assignment Sections Completed:**
- ✅ Section 1: Backend Architecture & Normalization Engine
- ✅ Section 2: Analyst Review Dashboard (React UI)
- ✅ Section 3: Deployment Readiness & Engineering Documentation

---

## Engineering Documentation
High-quality engineering documentation explaining the rationale behind the architecture can be found in the `docs/` folder:
- [MODEL.md](./docs/MODEL.md) — Database schema, multi-tenancy, and normalization architecture.
- [DECISIONS.md](./docs/DECISIONS.md) — Key technical judgments and ambiguities resolved.
- [TRADEOFFS.md](./docs/TRADEOFFS.md) — Features intentionally omitted and how they would scale in production.
- [SOURCES.md](./docs/SOURCES.md) — Research into the real-world formatting of SAP/Utility/Travel data.

---

## Reviewer Demo Flow

To evaluate the platform, follow this workflow:

1. **Dashboard Overview:** 
   Open the React frontend. Note the KPIs on the Dashboard.
2. **Uploads History:**
   Navigate to "Data Uploads". You will see that three batches of data have already been ingested (SAP, Utility, Travel). This demonstrates the backend ingestion services parsed the files successfully.
3. **Analyst Review (The Core Feature):**
   Navigate to "Normalized Records". This table shows the successfully parsed records.
4. **Identify Suspicious Records:**
   Notice the records flagged with a red "Suspicious" badge. The backend statistical engine flagged these because their CO2e deviated by more than 3 standard deviations from the batch mean.
5. **Traceability in Action:**
   Click on any record to open the Slide-out Panel. 
   - Observe the exact mathematical calculation (Value × Factor = CO2e).
   - Observe the **Source Traceability** terminal block at the bottom. It shows the exact, unmutated JSON representing the messy CSV row that generated this record.
6. **Audit & Approval:**
   Click "Approve Record". The status updates immediately. In the backend, a Django signal automatically captures the JSON diff and writes it to the immutable `AuditLog` table.

---

## Deployment & Hosting

This project is configured to be deployed on **Render.com** using Infrastructure-as-Code.

### Included Production Configuration
- `render.yaml`: Blueprint defining the PostgreSQL database, Django backend, and React static site.
- `build.sh`: Unified build script running migrations and collectstatic.
- `breatheESG/settings.py`: Configured with `whitenoise` for static files, `dj-database-url` for connection strings, and secure CORS headers.
- `frontend/vite.config.js`: Configured to inject the live API URL during build.

### How to Deploy
1. Push this repository to your personal GitHub account.
2. Create an account on [Render.com](https://render.com).
3. Click **New > Blueprint**.
4. Connect your GitHub account and select this repository.
5. Render will read the `render.yaml` file and automatically spin up the database, backend, and frontend.

---

## Local Development Setup

If you prefer to run the project locally instead of deploying:

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### 1. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
# (Copy .env.example to .env and configure your local postgres credentials)
cp .env.example .env

# Run migrations and seed the database with mock data
python manage.py migrate
python manage.py seed_data

# Start server
python manage.py runserver
```

### 2. Frontend Setup
Open a new terminal:
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`, proxying API requests to the Django backend.
