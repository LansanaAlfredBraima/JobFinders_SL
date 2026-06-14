# Job Opportunity REST API for Youth Employment (Group E Project)

**Limkokwing University of Creative Technology**  
*Faculty of Information & Communications Technology*  
*Course Project: Secure, Scalable, and Professional-Grade REST API*  

---

## 1. Executive Summary & SDG Alignment

The **Job Opportunity API** is an open-source, scalable, and secure REST web service built using **FastAPI** and **PostgreSQL** to match job-seeking youth with micro, small, and medium enterprises (MSMEs). 

This project aligns directly with **UN Sustainable Development Goal (SDG) 8: Decent Work and Economic Growth**, specifically addressing:
* **Target 8.5**: Achieving full and productive employment and decent work for all youth.
* **Target 8.6**: Substantially reducing the proportion of youth not in employment, education, or training (NEET).
* **Digital Public Goods (DPG)** compliance: Adhering to platform independence, using open data standards (JSON/OpenAPI 3.0), and utilizing the MIT Open-Source License.

---

## 2. Key Architecture & Features

- **Asynchronous Execution**: Fully utilizes `async/await` syntax paired with standard asynchronous PostgreSQL operations (`asyncpg` driver + SQLAlchemy 2.0 `AsyncSession`) to maximize request throughput.
- **Stateless JWT Security (OAuth2)**: Employs signed JSON Web Tokens for stateless user authentication.
- **Role-Based Access Control (RBAC)**: Protects resources based on defined user roles:
  * **Seeker**: Can search listings, modify their personal seeker profile, and apply to listings.
  * **Employer**: Can post jobs, edit/delete their own listings, and review/update applications.
  * **Admin**: Has full database CRUD administrative capabilities.
- **Secure Document Uploads**: Implements strict security validations for resume uploads:
  * File size limits enforced at 5MB.
  * MIME type validations (accepts `application/pdf` only).
  * Filename sanitization to mitigate path traversal and injection attacks.
- **Direct Cryptography**: Employs direct `bcrypt` password hashing to optimize execution performance and ensure native package compatibility on modern Python interpreters.

---

## 3. Project Directory Structure

```
├── .env                  # Development environment configurations
├── .env.example          # Environment configuration template
├── requirements.txt      # Project dependencies
├── config.py             # Type-safe configuration loader using Pydantic Settings
├── database.py           # Asynchronous SQLAlchemy connection & session manager
├── models.py             # Database relational models (SQLAlchemy 2.0)
├── schemas.py            # Input validation and serialization models (Pydantic V2)
├── auth.py               # Cryptography, JWT verification, and RBAC guards
├── crud.py               # Asynchronous database query implementation
├── main.py               # FastAPI application runner & CORS middleware setup
├── Dockerfile            # Container configuration for standard deployment
├── verify_api.py         # 20-step automated validation test suite
└── uploads/              # Local storage directory for uploaded PDF resumes (auto-created)
```

---

## 4. REST API Endpoint Reference

All endpoints strictly use pluralized nouns, predictable resource paths, and standard REST HTTP methods:

| HTTP Method | Endpoint | Access Level | Description | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/register` | Public | Register a Seeker or Employer | `201`, `400` |
| **POST** | `/api/v1/auth/login` | Public | Authenticate credentials & get JWT token | `200`, `401` |
| **GET** | `/api/v1/auth/me` | Authenticated | Retrieve current user profile details | `200`, `401` |
| **PUT** | `/api/v1/auth/profile` | Authenticated (Seeker) | Update Seeker profile attributes | `200`, `401`, `403` |
| **GET** | `/api/v1/jobs` | Public | Retrieve paginated list of active jobs (filterable) | `200` |
| **GET** | `/api/v1/jobs/{id}` | Public | Retrieve single job details by ID | `200`, `404` |
| **POST** | `/api/v1/jobs` | Authenticated (Employer) | Create a new job opportunity listing | `201`, `403` |
| **PUT** | `/api/v1/jobs/{id}` | Authenticated (Employer Owner) | Update details of an existing job listing | `200`, `403`, `404` |
| **DELETE** | `/api/v1/jobs/{id}` | Authenticated (Employer Owner / Admin) | Delete/Close a job listing | `204`, `403`, `404` |
| **POST** | `/api/v1/jobs/{id}/apply` | Authenticated (Seeker) | Submit application with PDF resume upload | `201`, `400`, `401` |
| **GET** | `/api/v1/applications` | Authenticated | View submitted applications (Context-aware) | `200`, `401` |
| **PATCH** | `/api/v1/applications/{id}` | Authenticated (Employer Owner) | Update application status (e.g. `interviewing`) | `200`, `403`, `404` |

---

## 5. Local Setup & Installation

### Prerequisites
* Python 3.8+
* PostgreSQL server running locally or accessible via network.

### Step 1: Clone the Repository & Configure Environment
1. Copy `.env.example` into a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and set your PostgreSQL parameters:
   ```env
   DATABASE_URL=postgresql+asyncpg://<username>:<password>@<host>:<port>/JobLinkUs
   ```

### Step 2: Establish Virtual Environment & Install Packages
```bash
# Create environment
# On macOS/Linux:
python3 -m venv .venv
# On Windows:
python -m venv .venv

# Activate environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
.venv\Scripts\activate.bat

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run the Development Server
Launch the ASGI server using uvicorn:
```bash
uvicorn main:app --reload
```
Once started, you can immediately access:
* **Interactive Swagger UI Docs**: [http://localhost:8000/](http://localhost:8000/) (automatically redirected) or [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc System**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

*Note: Database tables are automatically generated on application startup, so no manual migrations are needed.*

---

## 6. Containerized Deployment (Docker)

To run the application inside docker containers for maximum portability and data separation:

1. **Build the Container**:
   ```bash
   docker build -t job-api .
   ```
2. **Run the Container**:
   ```bash
   docker run -d -p 8000:8000 --name job-api-instance --env-file .env job-api
   ```
The container exposes the REST endpoints on port `8000`.

---

## 7. Running the Verification Suite

A 20-step automated validation test suite has been provided to test authentication, job search queries, PDF limit triggers, and RBAC policies:

```bash
# Ensure virtual environment is active
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\Activate.ps1

# Run the test suite
python verify_api.py
```
This script resets the test schemas, populates clean mock records, executes 20 rigorous test scenarios sequentially, and logs operations directly to the console.
