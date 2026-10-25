"""FastAPI application for managing student records."""

import re
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.database import DATABASE_PATH, get_connection, initialize_database


class StudentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    student_id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=120)
    date_of_birth: date
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=30)
    course: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validate_contact(self):
        if not self.email and not self.phone:
            raise ValueError("Provide at least an email address or phone number")
        if self.email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", self.email):
            raise ValueError("Enter a valid email address")
        return self


class Student(StudentInput):
    model_config = ConfigDict(from_attributes=True)


def create_app(database_path: Path | str = DATABASE_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database(database_path)
        yield

    app = FastAPI(
        title="Students Database CRUD API",
        description="A simple API for creating and managing student records.",
        version="1.0.0",
        lifespan=lifespan,
    )

    def connection_dependency():
        yield from get_connection(database_path)

    Connection = Annotated[sqlite3.Connection, Depends(connection_dependency)]

    @app.get("/", tags=["health"])
    def read_root():
        return {"message": "Students Database CRUD API", "docs": "/docs"}

    @app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED, tags=["students"])
    def create_student(student: StudentInput, connection: Connection):
        try:
            connection.execute(
                "INSERT INTO students (student_id, name, date_of_birth, email, phone, course, address) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (student.student_id, student.name, student.date_of_birth.isoformat(), student.email,
                 student.phone, student.course, student.address),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise HTTPException(status_code=409, detail="A student with this ID already exists") from exc
            raise HTTPException(status_code=422, detail="Student record violates a database constraint") from exc
        return student

    @app.get("/students", response_model=list[Student], tags=["students"])
    def list_students(
        connection: Connection,
        name: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
        course: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    ):
        clauses, values = [], []
        if name:
            clauses.append("name LIKE ? COLLATE NOCASE")
            values.append(f"%{name}%")
        if course:
            clauses.append("course LIKE ? COLLATE NOCASE")
            values.append(f"%{course}%")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = connection.execute(f"SELECT * FROM students{where} ORDER BY student_id", values).fetchall()
        return [dict(row) for row in rows]

    @app.get("/students/{student_id}", response_model=Student, tags=["students"])
    def get_student(student_id: str, connection: Connection):
        row = connection.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Student not found")
        return dict(row)

    @app.put("/students/{student_id}", response_model=Student, tags=["students"])
    def update_student(student_id: str, student: StudentInput, connection: Connection):
        if student.student_id != student_id:
            raise HTTPException(status_code=422, detail="student_id in the body must match the URL")
        cursor = connection.execute(
            "UPDATE students SET name = ?, date_of_birth = ?, email = ?, phone = ?, course = ?, address = ? "
            "WHERE student_id = ?",
            (student.name, student.date_of_birth.isoformat(), student.email, student.phone,
             student.course, student.address, student_id),
        )
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        return student

    @app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["students"])
    def delete_student(student_id: str, connection: Connection):
        cursor = connection.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
