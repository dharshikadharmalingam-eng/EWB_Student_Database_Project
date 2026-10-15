# EWB Students Database CRUD API

A Python backend project built with **FastAPI** and **SQLite** for managing student records. It implements Create, Read, Update, and Delete (CRUD), input validation, duplicate-email handling, and persistent local storage.

## Features

- Create a student record
- List and filter students by name or course
- Retrieve a student by ID
- Replace a record with `PUT`
- Partially update a record with `PATCH`
- Delete a record
- SQLite database created automatically at startup
- Request validation with Pydantic
- Helpful HTTP status codes and missing-record handling
- Interactive API docs at `/docs`

## Requirements

- Python 3.10 or later
- pip

## Setup

### Windows (PowerShell)

```powershell
cd ewb-students-crud
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

### macOS / Linux

```bash
cd ewb-students-crud
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:
- API welcome page: http://127.0.0.1:8000/
- Interactive Swagger documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

The `students.db` SQLite file is created automatically beside `main.py` when the app starts. Data remains after the server restarts.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/students` | Create a student |
| `GET` | `/students` | List students |
| `GET` | `/students?name=asha` | Filter by name |
| `GET` | `/students?course=computer` | Filter by course |
| `GET` | `/students/{student_id}` | Get one student |
| `PUT` | `/students/{student_id}` | Replace editable fields |
| `PATCH` | `/students/{student_id}` | Update only supplied fields |
| `DELETE` | `/students/{student_id}` | Delete a student |

List endpoint also supports pagination, for example `/students?limit=20&offset=0`.

## Test the API

You can run these requests in the interactive docs at `http://127.0.0.1:8000/docs`.

### 1. Create a student

Select `POST /students` → **Try it out** and submit:

```json
{
  "name": "Asha Kumar",
  "date_of_birth": "2005-06-15",
  "email": "asha.demo@example.com",
  "phone": "9876543210",
  "course": "Computer Science",
  "address": "Chennai"
}
```

A successful creation returns status `201 Created` and a generated student ID.

### 2. List students

Send `GET /students`. Use the ID returned from the create response for the following requests.

### 3. Get one student

Send `GET /students/1` (replace `1` with the actual ID).

### 4. Update one field

Send `PATCH /students/1` with:

```json
{
  "course": "Information Technology"
}
```

Only the provided field changes.

### 5. Replace a student's editable fields

Send `PUT /students/1` with all required fields, using the actual student ID.

### 6. Delete a student

Send `DELETE /students/1`. A successful deletion returns status `204 No Content`.

## Validation and error handling

- Name must be 2–100 characters and cannot be blank.
- Date of birth must be in the past.
- Email must have a valid email format and must be unique.
- Phone is optional and checked for common phone characters.
- Optional course and address fields have maximum lengths.
- Invalid request bodies return `422 Unprocessable Entity`.
- Missing student IDs return `404 Not Found`.
- Duplicate emails return `409 Conflict`.
- An empty PATCH request returns `400 Bad Request`.

## Security and privacy notes

- Use synthetic/demo student information only.
- Do not commit `students.db`, passwords, tokens, or real student personal information.
- SQL queries use parameterized values to help prevent SQL injection.
- The API does not include authentication or authorization. Add access controls before deploying it for real student data.
- Run locally for assignment demonstrations; do not expose it publicly with real personal information.

## Implementation overview

1. FastAPI receives and validates HTTP requests.
2. Pydantic models define accepted request fields and validation rules.
3. Python's built-in `sqlite3` module reads and writes records.
4. SQLite persists data in `students.db`.
5. FastAPI serializes responses and generates the Swagger API documentation.

## Optional future enhancement

The assignment mentions an optional local Ollama extension. It is intentionally not included in this core version; the CRUD application is the required priority.
