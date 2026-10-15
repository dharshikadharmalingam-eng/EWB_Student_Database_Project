from contextlib import asynccontextmanager, contextmanager
from datetime import date
from pathlib import Path
import re
import sqlite3
from typing import Iterator, Optional

from fastapi import FastAPI, HTTPException, Path as ApiPath, Query, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "students.db"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection with named-row access and close it reliably."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the students table if it does not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL CHECK(length(name) BETWEEN 2 AND 100),
                date_of_birth TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                phone TEXT,
                course TEXT,
                address TEXT,
                enrollment_date TEXT NOT NULL
            )
            """
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="EWB Students Database API",
    description="A student-record management API built with FastAPI and SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)


class StudentBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100, examples=["Asha Kumar"])
    date_of_birth: date = Field(examples=["2005-06-15"])
    email: EmailStr = Field(examples=["asha@example.com"])
    phone: Optional[str] = Field(default=None, max_length=20, examples=["9876543210"])
    course: Optional[str] = Field(default=None, max_length=100, examples=["Computer Science"])
    address: Optional[str] = Field(default=None, max_length=250)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Name cannot be blank.")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError("Date of birth must be in the past.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            if value and not re.fullmatch(r"[0-9+\-() ]{7,20}", value):
                raise ValueError("Phone must contain 7–20 digits or common phone symbols.")
            return value or None
        return value


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    """Partial update model: every field is optional."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=20)
    course: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=250)

    @field_validator("name", "date_of_birth", "email", mode="before")
    @classmethod
    def reject_null_required_fields(cls, value: object) -> object:
        if value is None:
            raise ValueError("This field cannot be null.")
        return value

    @field_validator("name")
    @classmethod
    def validate_optional_name(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Name cannot be blank.")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_optional_birth_date(cls, value: Optional[date]) -> Optional[date]:
        if value is not None and value >= date.today():
            raise ValueError("Date of birth must be in the past.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_optional_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            value = value.strip()
            if value and not re.fullmatch(r"[0-9+\-() ]{7,20}", value):
                raise ValueError("Phone must contain 7–20 digits or common phone symbols.")
            return value or None
        return value


class StudentResponse(BaseModel):
    id: int
    name: str
    date_of_birth: date
    email: EmailStr
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: date


def row_to_student(row: sqlite3.Row) -> dict:
    """Convert a database row to JSON-friendly values."""
    result = dict(row)
    return result


def ensure_student_exists(connection: sqlite3.Connection, student_id: int) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM students WHERE id = ?", (student_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} was not found.",
        )
    return row


@app.get("/", tags=["General"])
def home():
    return {
        "message": "Welcome to the EWB Students Database API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "healthy"}


@app.post(
    "/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Students"],
)
def create_student(student: StudentCreate):
    enrollment_date = date.today().isoformat()
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO students
                    (name, date_of_birth, email, phone, course, address, enrollment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student.name,
                    student.date_of_birth.isoformat(),
                    str(student.email),
                    student.phone,
                    student.course,
                    student.address,
                    enrollment_date,
                ),
            )
            row = connection.execute(
                "SELECT * FROM students WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return row_to_student(row)
    except sqlite3.IntegrityError as exc:
        if "email" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A student with this email address already exists.",
            ) from exc
        raise HTTPException(status_code=400, detail="Could not create student.") from exc


@app.get("/students", response_model=list[StudentResponse], tags=["Students"])
def list_students(
    name: Optional[str] = Query(default=None, min_length=1, max_length=100),
    course: Optional[str] = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    query = "SELECT * FROM students WHERE 1 = 1"
    parameters: list = []

    if name:
        query += " AND name LIKE ? COLLATE NOCASE"
        parameters.append(f"%{name}%")
    if course:
        query += " AND course LIKE ? COLLATE NOCASE"
        parameters.append(f"%{course}%")

    query += " ORDER BY id LIMIT ? OFFSET ?"
    parameters.extend([limit, offset])

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()
        return [row_to_student(row) for row in rows]


@app.get("/students/{student_id}", response_model=StudentResponse, tags=["Students"])
def get_student(student_id: int = ApiPath(..., ge=1)):
    # This route is retained as a separate function for clear API documentation.
    with get_connection() as connection:
        row = ensure_student_exists(connection, student_id)
        return row_to_student(row)


@app.put("/students/{student_id}", response_model=StudentResponse, tags=["Students"])
def replace_student(student_id: int, student: StudentCreate):
    """Replace all editable student fields (PUT)."""
    try:
        with get_connection() as connection:
            ensure_student_exists(connection, student_id)
            connection.execute(
                """
                UPDATE students
                SET name = ?, date_of_birth = ?, email = ?, phone = ?, course = ?, address = ?
                WHERE id = ?
                """,
                (
                    student.name,
                    student.date_of_birth.isoformat(),
                    str(student.email),
                    student.phone,
                    student.course,
                    student.address,
                    student_id,
                ),
            )
            row = ensure_student_exists(connection, student_id)
            return row_to_student(row)
    except sqlite3.IntegrityError as exc:
        if "email" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A student with this email address already exists.",
            ) from exc
        raise HTTPException(status_code=400, detail="Could not update student.") from exc


@app.patch("/students/{student_id}", response_model=StudentResponse, tags=["Students"])
def update_student(student_id: int, student: StudentUpdate):
    """Update only the fields supplied (PATCH)."""
    updates = student.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update.")

    for key, value in updates.items():
        if isinstance(value, date):
            updates[key] = value.isoformat()
        elif key == "email" and value is not None:
            updates[key] = str(value)

    allowed_columns = {"name", "date_of_birth", "email", "phone", "course", "address"}
    if not set(updates).issubset(allowed_columns):
        raise HTTPException(status_code=400, detail="Invalid update field.")

    assignments = ", ".join(f"{column} = ?" for column in updates)
    values = list(updates.values()) + [student_id]

    try:
        with get_connection() as connection:
            ensure_student_exists(connection, student_id)
            connection.execute(
                f"UPDATE students SET {assignments} WHERE id = ?", values
            )
            row = ensure_student_exists(connection, student_id)
            return row_to_student(row)
    except sqlite3.IntegrityError as exc:
        if "email" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A student with this email address already exists.",
            ) from exc
        raise HTTPException(status_code=400, detail="Could not update student.") from exc


@app.delete(
    "/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Students"],
)
def delete_student(student_id: int):
    with get_connection() as connection:
        ensure_student_exists(connection, student_id)
        connection.execute("DELETE FROM students WHERE id = ?", (student_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
