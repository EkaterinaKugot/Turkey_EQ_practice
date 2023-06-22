from pydantic import EmailStr, BaseModel
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import os

import zipfile
import shutil

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime

SQLALCHEMY_DATABASE_URL = "sqlite:///./app/db/eq_monitor.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

api = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Schema FastAPI
class UserOut(BaseModel):
    email: EmailStr

    class Config:
        orm_mode = True


class UserIn(UserOut):
    password: str


class FileOut(BaseModel):
    user_id: int
    path: str
    start_date: str
    end_date: str
    upload_date: str


# Model DB
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    files = relationship("FileDB", back_populates="user")


class FileDB(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    path = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    upload_date = Column(DateTime, nullable=False)
    user = relationship("UserDB", back_populates="files")


Base.metadata.create_all(bind=engine)


# CRUD
def create_user_db(db: Session, user: UserIn):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = UserDB(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(UserDB).filter(UserDB.email == email).first()


def update_user_email_db(db: Session, email: str, new_email: str):
    db_user = get_user_by_email(db, email)
    db_user.email = new_email
    db.commit()
    return db_user


def delete_user_db(db: Session, user: UserIn):
    db_user = get_user_by_email(db, user.email)
    db.delete(db_user)
    db.commit()


def upload_file_db(db: Session, file: FileOut):
    db_file = FileDB(user_id=file.user_id, path=file.path)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_all_files_db(db: Session, user: UserIn):
    db_user = get_user_by_email(db, user.email)
    return db.query(FileDB).filter(FileDB.user_id == db_user.id).all()


# Endpoints
@api.post("/users/", response_model=UserOut)
def create_user(user: UserIn, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = create_user_db(db=db, user=user)
    directory = f"./app/users/user{db_user.id}"
    if not os.path.exists(directory):
        os.mkdir(directory)
    return db_user


@api.post("/users/", response_model=UserOut)
def update_user_email(new_email: EmailStr, user: UserIn, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user is None:
        raise HTTPException(status_code=400, detail="This email does not exist")
    elif (user.password + "notreallyhashed" != db_user.hashed_password):
        raise HTTPException(status_code=400, detail="The password was entered incorrectly")
    else:
        return update_user_email_db(db, user.email, new_email)


@api.delete("/users/")
def delete_user(user: UserIn, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user is None:
        raise HTTPException(status_code=400, detail="This email does not exist")
    elif (user.password + "notreallyhashed" != db_user.hashed_password):
        raise HTTPException(status_code=400, detail="The password was entered incorrectly")
    else:
        delete_user_db(db, user)
        return None


@api.post("/files/")
def upload_file(emailIn: EmailStr, passwordIn: str, up_file: UploadFile, dirname: str, db: Session = Depends(get_db)):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, email=user.email)
    if db_user is None:
        db_user = create_user(user, db)
    elif (user.password + "notreallyhashed" != db_user.hashed_password):
        raise HTTPException(status_code=400, detail="The password was entered incorrectly")

    directory = f"./app/users/user{db_user.id}/{dirname}"
    if not os.path.exists(directory):
        os.mkdir(directory)

    # сохраняем файл
    f = open(directory + f"/{up_file.filename}", 'wb')
    f.write(up_file.file.read())
    f.close()

    fileOut = FileOut(user_id=db_user.id, path=directory + f"/{up_file.filename}")
    return upload_file_db(db, fileOut)


@api.get("/files/")
def get_all_files(emailIn: EmailStr, passwordIn: str, db: Session = Depends(get_db)):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, user.email)
    if db_user is None:
        raise HTTPException(status_code=400, detail="This email does not exist")
    elif (user.password + "notreallyhashed" != db_user.hashed_password):
        raise HTTPException(status_code=400, detail="The password was entered incorrectly")
    else:
        return get_all_files_db(db, user)


@api.post("/upload_archive/")
def upload_files(up_file: UploadFile):

    directory = f"./files"

    # сохранение файлов
    file_name = up_file.filename
    f = open(directory + f"/{file_name}", 'wb')
    f.write(up_file.file.read())
    f.close()

    if file_name.split('.')[-1] == 'zip':
        with zipfile.ZipFile(directory + f"/{file_name}", 'r') as zip_ref:
            uploaded_files = [x for x in zip_ref.namelist() if not x.endswith('/')]
            dirs = [x for x in zip_ref.namelist() if x.endswith('/')]
            zip_ref.extractall(directory)
        for i in range(len(uploaded_files)):
            uploaded_files[i] = uploaded_files[i].split('/')[-1]
        if len(dirs) != 0:
            uploaded_files = []
            for file in os.listdir(directory + f"/{dirs[0]}"):
                # Если такой файл существует, то старый файл удалится и заменится новым
                if os.path.exists(os.path.join(directory, file)):
                    os.remove(os.path.join(directory, file))
                    shutil.move(directory + f"/{dirs[0]}{file}", directory)

                # Если такой файл уже существует, то новый добавится
                # с цифрой означающей номер копии
                # number_of_copies = 1
                # original_name = file
                # while os.path.exists(os.path.join(directory, file)):
                #   number_of_copies += 1
                #  file = f"{'.'.join(original_name.split('.')[:-1])}_{number_of_copies}.{original_name.split('.')[-1]}"
                # if number_of_copies > 1:
                #   os.rename(directory + f"/{dirs[0]}{original_name}", directory + f"/{file}")
                # else:
                #   shutil.move(directory + f"/{dirs[0]}{file}", directory)
                uploaded_files.append(file)
            os.rmdir(os.path.join(directory, dirs[0]))
        os.remove(os.path.join(directory, file_name))
    else:
        uploaded_files = [file_name]

    for i in uploaded_files:
        i = i
    return {'message': "file uploaded", 'files': uploaded_files}
