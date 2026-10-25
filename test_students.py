from fastapi.testclient import TestClient

from app.main import create_app


def make_client(tmp_path):
    app = create_app(tmp_path / "test_students.db")
    return TestClient(app)


def sample_student(**overrides):
    student = {
        "student_id": "STU-1001",
        "name": "Asha Rao",
        "date_of_birth": "2005-04-12",
        "email": "asha@example.com",
        "course": "Computer Science",
        "address": "12 Demo Street",
    }
    return {**student, **overrides}


def test_create_list_filter_get_update_delete(tmp_path):
    with make_client(tmp_path) as client:
        created = client.post("/students", json=sample_student())
        assert created.status_code == 201
        assert created.json()["student_id"] == "STU-1001"
        assert created.json()["date_of_birth"] == "2005-04-12"

        listed = client.get("/students")
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        filtered = client.get("/students", params={"course": "computer"})
        assert len(filtered.json()) == 1
        assert client.get("/students", params={"name": "Nobody"}).json() == []

        fetched = client.get("/students/STU-1001")
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "Asha Rao"

        updated = client.put(
            "/students/STU-1001",
            json=sample_student(name="Asha R.", phone="+1-555-0100", email=None),
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "Asha R."
        assert updated.json()["phone"] == "+1-555-0100"

        deleted = client.delete("/students/STU-1001")
        assert deleted.status_code == 204
        assert client.get("/students/STU-1001").status_code == 404


def test_duplicate_student_id_returns_conflict(tmp_path):
    with make_client(tmp_path) as client:
        assert client.post("/students", json=sample_student()).status_code == 201
        duplicate = client.post("/students", json=sample_student(name="Another Student"))
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"] == "A student with this ID already exists"


def test_missing_student_operations_return_not_found(tmp_path):
    with make_client(tmp_path) as client:
        assert client.get("/students/absent").status_code == 404
        assert client.put("/students/absent", json=sample_student(student_id="absent")).status_code == 404
        assert client.delete("/students/absent").status_code == 404


def test_invalid_inputs_return_validation_errors(tmp_path):
    with make_client(tmp_path) as client:
        assert client.post("/students", json=sample_student(date_of_birth="not-a-date")).status_code == 422
        assert client.post("/students", json=sample_student(email="invalid-email")).status_code == 422
        no_contact = sample_student()
        no_contact.pop("email")
        assert client.post("/students", json=no_contact).status_code == 422
        assert client.put("/students/STU-1001", json=sample_student(student_id="OTHER")).status_code == 422


def test_records_persist_between_app_instances(tmp_path):
    database_path = tmp_path / "persistent.db"
    with TestClient(create_app(database_path)) as first_client:
        assert first_client.post("/students", json=sample_student()).status_code == 201
    with TestClient(create_app(database_path)) as second_client:
        response = second_client.get("/students/STU-1001")
        assert response.status_code == 200
        assert response.json()["email"] == "asha@example.com"
