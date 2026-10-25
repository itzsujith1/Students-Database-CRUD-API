# Students Database CRUD Application

A small student-record API built with Python, FastAPI, and SQLite. It supports creating, listing/filtering, retrieving, updating, and deleting student records. The optional Ollama extension is intentionally not included.

## Requirements

- Python 3.10 or newer
- pip

## Setup

From this project folder, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the API

```powershell
python -m uvicorn app.main:app --reload
```

Open the interactive API documentation at <http://127.0.0.1:8000/docs>. SQLite creates `students.db` in the project folder on first startup. The database file is excluded from Git.

## API

Student fields: `student_id` (unique string), `name`, `date_of_birth` (`YYYY-MM-DD`), at least one of `email` or `phone`, and optional `course` and `address`.

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/students` | Create a student (returns `201`) |
| GET | `/students` | List students; optional `name` and `course` substring filters |
| GET | `/students/{student_id}` | Retrieve one student |
| PUT | `/students/{student_id}` | Replace a student's details |
| DELETE | `/students/{student_id}` | Delete a student (returns `204`) |

Duplicate IDs return `409`; missing records return `404`; invalid input returns `422` with validation details. For PUT, the ID in the JSON body must match the ID in the URL.

## Example requests

Create a dummy student:

```powershell
curl.exe -X POST http://127.0.0.1:8000/students `
  -H "Content-Type: application/json" `
  -d '{"student_id":"STU-1001","name":"Asha Rao","date_of_birth":"2005-04-12","email":"asha@example.com","course":"Computer Science","address":"12 Demo Street"}'
```

Example response (`201 Created`):

```json
{
  "student_id": "STU-1001",
  "name": "Asha Rao",
  "date_of_birth": "2005-04-12",
  "email": "asha@example.com",
  "phone": null,
  "course": "Computer Science",
  "address": "12 Demo Street"
}
```

List or filter:

```text
GET http://127.0.0.1:8000/students?course=Computer
```

Get, update, and delete:

```text
GET    http://127.0.0.1:8000/students/STU-1001
PUT    http://127.0.0.1:8000/students/STU-1001
DELETE http://127.0.0.1:8000/students/STU-1001
```

PUT uses the same JSON shape as POST. These examples use dummy data only.

## Tests

```powershell
python -m pytest -v
```

Tests use temporary SQLite databases and do not modify your local `students.db`.
