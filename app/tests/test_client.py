from pydantic import EmailStr
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..endpoints import *

user_dir.user_dir = "./app/tests/users/user"

SQLALCHEMY_DATABASE_URL = "sqlite:///./app/tests/test_db.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


api.dependency_overrides[get_db] = override_get_db
client = TestClient(api)


def test_create_user():
    user = {"email": "user@example.com", "password": 'qwer'}
    response = client.post("/users/", json=user)
    assert response.status_code == 200
    assert response.json() == {"email": "user@example.com"}

    response = client.post("/users/", json=user)
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}


def test_update_user_email():
    user = {"email": "user@example.com", "password": 'asdf'}
    response = client.put("/users/?new_email=test_user%40example.com", json=user)
    assert response.status_code == 400
    assert response.json() == {"detail": "The password was entered incorrectly"}

    user = {"email": "user@example.com", "password": 'qwer'}
    response = client.put("/users/?new_email=test_user%40example.com", json=user)
    assert response.status_code == 200
    assert response.json() == {"email": "test_user@example.com"}

    user = {"email": "tester@example.com", "password": 'qwer'}
    response = client.put("/users/?new_email=test_user%40example.com", json=user)
    assert response.status_code == 400
    assert response.json() == {"detail": "This email does not exist"}


def test_upload_file():
    URL = "/files/?emailIn=test_user%40example.com&passwordIn=qwer&startDate=2023-06-22%2019%3A40%3A46.486583&endDate=" \
          "2023-06-22%2019%3A40%3A46.486583"
    file = {"up_file": ("file.txt", open("./app/tests/test files/file.txt", "rb"), "text/plain")}
    response = client.post(URL, files=file)
    assert response.status_code == 200
    assert response.json() == ['file.txt']

    for file_name in ["test files", "test files with folder"]:
        file = {"up_file": (f"{file_name}.zip", open(f"./app/tests/test files/{file_name}.zip", "rb"),
                            "application/zip")}
        response = client.post(URL, files=file)
        assert response.status_code == 200
        assert response.json() == ['file1.txt', 'file2.txt']


def test_get_last_files():
    response = client.get("/files/last?emailIn=test_user%40example.com&passwordIn=qwer")
    assert response.status_code == 200


def test_delete_file():
    user = {"email": "test_user@example.com", "password": 'qwer'}
    responce = client.request("DELETE", "/files/?date=2023-06-22", json=user)
    assert responce.status_code == 200


def test_delete_user():
    user = {"email": "test_user@example.com", "password": 'asdf'}
    response = client.request("DELETE", "/users/", json=user)
    assert response.status_code == 400
    assert response.json() == {"detail": "The password was entered incorrectly"}

    user = {"email": "test_user@example.com", "password": 'qwer'}
    response = client.request("DELETE", "/users/", json=user)
    assert response.status_code == 200

    user = {"email": "tester@example.com", "password": 'qwer'}
    response = client.request("DELETE", "/users/", json=user)
    assert response.status_code == 400
    assert response.json() == {"detail": "This email does not exist"}
