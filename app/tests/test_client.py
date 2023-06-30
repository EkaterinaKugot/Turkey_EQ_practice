from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..main import *
import os


if not os.path.exists(os.path.join("./app/tests/users")):
    os.mkdir('./app/tests/users')

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
    URL = "/files/?emailIn=test_user%40example.com&passwordIn=asdf&startDate=2023-09-10%2012%3A13%3A00&endDate=" + \
          "2023-09-10%2017%3A23%3A00&type=ROTI&epc_date=2023-09-10%2017%3A23%3A00&epc_lat=34.0305&epc_lon=56.254"
    file = {"up_file": ("roti_10_24.h5", open("./app/tests/test files/roti_10_24.h5", "rb"), "text/plain")}
    response = client.post(URL, files=file)
    assert response.status_code == 400
    assert response.json() == {"detail": "The password was entered incorrectly"}

    URL = "/files/?emailIn=user%40example.com&passwordIn=qwer&startDate=2023-09-10%2012%3A13%3A00&endDate=" + \
          "2023-09-10%2017%3A23%3A00&type=2-10%20minute%20TEC%20variations&epc_date=2023-09-10%2017%3A23%3A00&" + \
          "epc_lat=34.0305&epc_lon=56.254"
    file = {"up_file": ("roti_10_24.h5", open("./app/tests/test files/roti_10_24.h5", "rb"), "text/plain")}
    response = client.post(URL, files=file)
    assert response.status_code == 200
    assert response.json() == ['roti_10_24.h5']
    assert os.path.exists(os.path.join("./app/tests/users/user2/", "roti_10_24.h5"))

    URL = "/files/?emailIn=test_user%40example.com&passwordIn=qwer&startDate=2023-09-10%2012%3A13%3A00&endDate=" + \
          "2023-09-10%2017%3A23%3A00&type=2-10%20variations&epc_date=2023-09-10%2017%3A23%3A00&" + \
          "epc_lat=34.0305&epc_lon=56.254"
    file = {"up_file": ("tnpgn_dtec_10_20_10_24.h5", open("./app/tests/test files/tnpgn_dtec_10_20_10_24.h5", "rb"),
                        "text/plain")}
    response = client.post(URL, files=file)
    assert response.status_code == 200
    assert response.json() == ['tnpgn_dtec_10_20_10_24.h5']
    assert os.path.exists(os.path.join("./app/tests/users/user1/", "tnpgn_dtec_10_20_10_24.h5"))

    URL = "/files/?emailIn=test_user%40example.com&passwordIn=qwer&startDate=2023-09-10%2012%3A13%3A00&endDate=" + \
          "2023-09-10%2017%3A23%3A00&type=2-10%20minute%20TEC%20variations&epc_date=2023-09-10%2017%3A23%3A00&" + \
          "epc_lat=34.0305&epc_lon=56.254"
    file = {"up_file": ("roti_10_24.h5", open("./app/tests/test files/roti_10_24.h5", "rb"), "text/plain")}
    response = client.post(URL, files=file)
    assert response.status_code == 200
    assert response.json() == ['roti_10_24.h5']
    assert os.path.exists(os.path.join("./app/tests/users/user1/", "roti_10_24.h5"))

    URL = "/files/?emailIn=test_user%40example.com&passwordIn=qwer&startDate=2023-09-10%2012%3A13%3A00&endDate=" + \
          "2023-09-10%2017%3A23%3A00&type=2-10%20minute%20TEC%20variations&epc_date=2023-09-10%2017%3A23%3A00&" + \
          "epc_lat=34.0305&epc_lon=22.254"
    file = {"up_file": ("tnpgn_dtec_2_10_10_24.h5", open("./app/tests/test files/tnpgn_dtec_2_10_10_24.h5", "rb"),
                        "text/plain")}
    response = client.post(URL, files=file)
    assert response.status_code == 200
    assert response.json() == ['tnpgn_dtec_2_10_10_24.h5']
    assert os.path.exists(os.path.join("./app/tests/users/user1/", "tnpgn_dtec_2_10_10_24.h5"))

    URL = "/files/?emailIn=test_user%40example.com&passwordIn=qwer&startDate=2023-09-10%2012%3A13%3A00&endDate=" + \
          "2023-09-10%2017%3A23%3A00&type=ROTI&epc_date=2023-09-10%2017%3A23%3A00&epc_lat=34.0305&epc_lon=56.254"
    for file_name in ["test files", "test files with folder"]:
        file = {"up_file": (f"{file_name}.zip", open(f"./app/tests/test files/{file_name}.zip", "rb"),
                            "application/zip")}
        response = client.post(URL, files=file)
        assert response.status_code == 200
        print(response.json())
        assert response.json() == ['dtec_2_10_10_24.h5', 'dtec_10_20_10_24.h5'] or \
               response.json() == ['dtec_10_20_10_24.h5', 'dtec_2_10_10_24.h5']
        assert os.path.exists(os.path.join("./app/tests/users/user1/", "dtec_2_10_10_24.h5"))
        assert os.path.exists(os.path.join("./app/tests/users/user1/", "dtec_10_20_10_24.h5"))


def test_get_last_files():
    response = client.get("/files/last?emailIn=test_user%40example.com&passwordIn=qwer")
    assert response.status_code == 200
    for path in response.json():
        assert path['path'] == './app/tests/users/user1/dtec_2_10_10_24.h5' or \
               path['path'] == './app/tests/users/user1/dtec_10_20_10_24.h5' or \
               path['path'] == './app/tests/users/user1/roti_10_24.h5' or \
               path['path'] == './app/tests/users/user1/tnpgn_dtec_2_10_10_24.h5' or \
               path['path'] == './app/tests/users/user1/tnpgn_dtec_10_20_10_24.h5'


def test_get_by_date():
    response = client.get("/files/?emailIn=test_user%40example.com&passwordIn=qwer&date=2023-09-10")
    assert response.status_code == 200
    for path in response.json():
        assert path['path'] == './app/tests/users/user1/dtec_2_10_10_24.h5' or \
               path['path'] == './app/tests/users/user1/dtec_10_20_10_24.h5' or \
               path['path'] == './app/tests/users/user1/roti_10_24.h5' or \
               path['path'] == './app/tests/users/user1/tnpgn_dtec_2_10_10_24.h5' or \
               path['path'] == './app/tests/users/user1/tnpgn_dtec_10_20_10_24.h5'

def test_draw_map():
    data = {
        "files": ["dtec_2_10_10_24.h5"],
        "date": ["2023-02-06T10:25:00.000Z", "2023-02-06T10:40:00.000Z", "2023-02-06T10:25:00.000Z"],
        "lat": [25],
        "lon": [25, 50],
        "c_limits": [[-0.1, 0.3]]
    }

    response = client.post("/map/?emailIn=test_user%40example.com&passwordIn=qwer", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "The number of elements is not equal to two"}

    data["lat"].append(25)
    response = client.post("/map/?emailIn=test_user%40example.com&passwordIn=qwer", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "the value is not a diagnosis"}

    data["lat"][1] = 50
    assert client.post("/map/?emailIn=test_user%40example.com&passwordIn=qwer", json=data).status_code == 200

    data["files"].append("file.h5")
    response = client.post("/map/?emailIn=test_user%40example.com&passwordIn=qwer", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "The file you selected is missing"}

    data["files"][1] = "dtec_2_10_10_24.h5"
    response = client.post("/map/?emailIn=test_user%40example.com&passwordIn=qwer", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Selected files of the same type"}

    data["files"][1] = "tnpgn_dtec_2_10_10_24.h5"
    response = client.post("/map/?emailIn=test_user%40example.com&passwordIn=qwer", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "The selected files must have the same data about the Epicenter"}

    data["files"][1] = "tnpgn_dtec_10_20_10_24.h5"
    data["files"].append("roti_10_24.h5")
    data["c_limits"].append([0.4, 0.1])
    response = client.post("/map/?emailIn=test_user%40example.com&passwordIn=qwer", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect number of elements in the color range"}

    data["files"].pop()
    response = client.post("/map/?emailIn=test_user%40example.com&passwordIn=qwer", json=data)
    assert response.status_code == 200

    data["date"].append("2023-02-06T10:25:00.000Z")
    response = client.post("/map/?emailIn=test_user%40example.com&passwordIn=qwer", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "The number of dates is incorrect"}


def test_delete_file():
    user = {"email": "test_user@example.com", "password": 'qwer'}
    responce = client.request("DELETE", "/files/?date=2023-09-10", json=user)
    assert responce.status_code == 200
    assert not os.path.exists(os.path.join("./app/tests/users/user1/", "dtec_2_10_10_24.h5"))
    assert not os.path.exists(os.path.join("./app/tests/users/user1/", "dtec_10_20_10_24.h5"))


def test_delete_user():
    user = {"email": "test_user@example.com", "password": 'asdf'}
    response = client.request("DELETE", "/users/", json=user)
    assert response.status_code == 400
    assert response.json() == {"detail": "The password was entered incorrectly"}

    user = {"email": "test_user@example.com", "password": 'qwer'}
    response = client.request("DELETE", "/users/", json=user)
    assert response.status_code == 200
    assert not os.path.exists("./app/tests/users/user1/")

    user = {"email": "user@example.com", "password": 'qwer'}
    response = client.request("DELETE", "/users/", json=user)
    assert response.status_code == 200
    assert not os.path.exists("./app/tests/users/user2/")

    user = {"email": "user@example.com", "password": 'qwer'}
    response = client.request("DELETE", "/users/", json=user)
    assert response.status_code == 400
    assert response.json() == {"detail": "This email does not exist"}
