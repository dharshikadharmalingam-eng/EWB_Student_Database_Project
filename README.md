# Students Database CRUD Application

A student-record management API built with Python, FastAPI, SQLite, and Pydantic. SQLite creates a persistent local database automatically when the application starts.

## Features

- Create, list, filter, retrieve, replace, partially update, and delete student records
- Pydantic validation for names, dates, email addresses, and optional contact fields
- Case-insensitive unique email addresses
- Appropriate HTTP errors for invalid input, duplicate email addresses, and missing records
- Interactive OpenAPI documentation

## Prerequisites

- Python 3.10 or later
- `pip`

SQLite is included with Python; no separate database server is required.

## Install and run

From the repository root in Windows PowerShell:

```powershell
cd ewb-students-crud
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

No virtual-environment activation or PowerShell execution-policy change is needed. On macOS or Linux, create a virtual environment with `python3 -m venv .venv`, install with `.venv/bin/python -m pip install -r requirements.txt`, and run with `.venv/bin/python -m uvicorn main:app --reload` from `ewb-students-crud`.

The local database is created as `ewb-students-crud/students.db` and is excluded from Git. Open the documentation at <http://127.0.0.1:8000/docs> or check <http://127.0.0.1:8000/health>.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/students` | Create a student (`201`) |
| `GET` | `/students` | List students; optional `name`, `course`, `limit`, and `offset` filters |
| `GET` | `/students/{student_id}` | Retrieve a student |
| `PUT` | `/students/{student_id}` | Replace editable student fields |
| `PATCH` | `/students/{student_id}` | Update supplied fields |
| `DELETE` | `/students/{student_id}` | Delete a student (`204`) |

Invalid input returns `422`, duplicate emails return `409`, and nonexistent IDs return `404`.

## Testing

Use Swagger UI at <http://127.0.0.1:8000/docs> to exercise each endpoint. Create records with synthetic data, then verify listing/filtering, retrieval, `PUT`, `PATCH`, and deletion. Also try an invalid email or future birth date (expect `422`), a duplicate email (expect `409`), and an unknown student ID (expect `404`). Delete any demo records after testing. The database persists between application restarts.

Do not use real student information or commit local database files, credentials, or secrets. This API has no authentication and is intended for local assignment demonstrations, not deployment with personal data.