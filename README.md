# ShareYou Dashboard

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql)
![AWS S3 / MinIO](https://img.shields.io/badge/AWS%20S3-569A31?style=for-the-badge&logo=amazon-s3)
![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-FF9900?style=for-the-badge&logo=aws-lambda)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)

## Project Description

ShareYou is a high-performance project management and secure file-sharing dashboard. Designed with a robust cloud-native architecture, it allows teams to create projects, invite participants via secure cryptographic links, and manage documents seamlessly.

Key Features:
- **Role-Based Access Control (RBAC):** Strict separation between Project Owners and Participants.
- **Data Integrity:** Transactional consistency across the PostgreSQL database and S3 file storage (rollback and cleanup protection).
- **Safe Concurrent Uploads:** Database row locking prevents Time-of-Check to Time-of-Use (TOCTOU) race conditions on project size limits.
- **Stateless Invites:** Cryptographic JWT-based invite links that require no temporary database storage.

---

## Architecture

Below is the visual architecture of the document upload flow.

> **Tip:** *Click on the diagram to expand and zoom in GitHub.*

```mermaid
flowchart TD
    %% Styling
    classDef client fill:#2a9d8f,stroke:#264653,stroke-width:2px,color:#fff,font-weight:bold,rx:10,ry:10;
    classDef backend fill:#e9c46a,stroke:#e76f51,stroke-width:2px,color:#333,font-weight:bold,rx:10,ry:10;
    classDef database fill:#f4a261,stroke:#e76f51,stroke-width:2px,color:#fff,font-weight:bold,rx:10,ry:10;
    classDef aws_s3 fill:#264653,stroke:#2a9d8f,stroke-width:2px,color:#fff,font-weight:bold,rx:10,ry:10;
    classDef aws_lambda fill:#e76f51,stroke:#f4a261,stroke-width:2px,color:#fff,font-weight:bold,rx:10,ry:10;

    %% Nodes
    Client(["Client (Browser/App)"]):::client
    
    subgraph Backend_System ["Backend System"]
        API["FastAPI Server"]:::backend
        DB[("PostgreSQL\n(Metadata & Users)")]:::database
    end
    
    subgraph AWS_Cloud ["AWS Cloud Infrastructure"]
        S3[("Amazon S3\n(Document Storage)")]:::aws_s3
        Lambda{"AWS Lambda\n(Event Trigger)"}:::aws_lambda
    end

    %% Connections
    Client -- "1. Upload File & Info" --> API
    API -- "2. Save Metadata\n(Transaction)" --> DB
    API -- "3. Stream File" --> S3
    
    %% Async Flow
    S3 -- "4. S3 Event Trigger" --> Lambda
    
    %% Lambda Processing
    Lambda -. "Antivirus Scan" .-> Lambda
    Lambda -. "File Size Check" .-> Lambda
    Lambda -. "File Type Validate" .-> Lambda
```

---

## Setup & Installation Instructions

Anyone can easily clone and run this project entirely through Docker.

### 1. Clone the repository
```bash
git clone https://github.com/HusseinAli234/share-you.git
cd share-you
```

### 2. Configure Environment Variables
Copy the `.env.example` file to create your local `.env`:
```bash
cp .env.example .env
```
*(The `.env` file is pre-configured with default values that work out-of-the-box with the local Docker setup).*

---

## How to Run

We use `docker compose` to effortlessly start the entire environment (FastAPI, PostgreSQL, and MinIO for local S3 simulation).

### Start the application
```bash
make up
```
*(Or manually run `docker compose up --build -d`)*

### Apply Database Migrations
Once the containers are running, you must initialize the database schema:
```bash
make migrate
```

Your API is now live!
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **MinIO S3 Console:** [http://localhost:9001](http://localhost:9001) (u: `minioadmin`, p: `minioadmin`)

### Stopping the application
```bash
make down
```

---

## How to Run Tests

The project has robust unit testing (96% Coverage) using `pytest`.

To run the full test suite locally:
```bash
# Create and activate a python virtual environment if you haven't
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the test suite
make test
```
*Tests use mocks for PostgreSQL and S3 to run instantly without requiring a live cloud connection.*

---

## API Overview

The API is fully documented via Swagger UI. Below is a high-level summary of the core endpoints:

### Auth
- `POST /auth/register` - Create a new user account.
- `POST /auth/login` - Authenticate and receive a JWT Bearer Token.

### Projects
- `POST /projects` - Create a new project (You automatically become the `Owner`).
- `GET /projects` - List all projects you have access to.
- `GET /projects/{project_id}` - View specific project details.
- `PUT /projects/{project_id}` - Update project info (Owners and Participants).
- `DELETE /projects/{project_id}` - Delete the project and all attached files (Owners only).

### Invites & Members
- `GET /projects/{project_id}/share?with={login}` - Generate a secure JWT invite link to invite `{login}` to the project (Owners only).
- `GET /projects/join?token={token}` - Public endpoint to decode the invite token and successfully join the project.

### Documents
- `POST /projects/{project_id}/documents` - Upload a document directly to S3. Limits are enforced.
- `GET /projects/{project_id}/documents` - List all project documents.
- `GET /projects/{project_id}/documents/{document_id}` - Get secure download URL for a specific document.
- `PUT /projects/{project_id}/documents/{document_id}` - Update/Replace an existing document.
- `DELETE /projects/{project_id}/documents/{document_id}` - Delete a document (Owners only).

---

## Make Commands Reference
- `make up` - Start Docker services.
- `make down` - Stop Docker services.
- `make build` - Rebuild Docker containers.
- `make logs` - View container logs.
- `make migrate` - Apply Alembic migrations.
- `make makemigrations` - Generate new Alembic migrations.
- `make test` - Run `pytest` suite.
- `make lint` - Check code style with `flake8`.
- `make format` - Format code with `black` and `isort`.
