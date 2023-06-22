from pydantic import EmailStr, BaseModel
from fastapi import FastAPI, Depends, HTTPException, UploadFile
import os
import shutil
from datetime import datetime, date 

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy import and_, or_, func

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

#Schema FastAPI
class UserOut(BaseModel):
    email: EmailStr
    
    class Config:
        orm_mode = True

class UserIn(UserOut):
    password: str


class FileOut(BaseModel):
    user_id: int
    path: str
    start_date: datetime
    end_date: datetime
    upload_date: datetime


#Model DB
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
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    upload_date = Column(String, nullable=False)
    user = relationship("UserDB", back_populates="files")
    
Base.metadata.create_all(bind=engine)

def input_data_error(db_user: UserDB, user: UserIn):
    if db_user is None:
        raise HTTPException(status_code=400, detail="This email does not exist")
    elif (user.password + "notreallyhashed" != db_user.hashed_password):
        raise HTTPException(status_code=400, detail="The password was entered incorrectly")
    

#CRUD
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
    user_data = db.query(FileDB).filter(FileDB.user_id == db_user.id).all()
    for data in user_data:
        db.delete(data)
    shutil.rmtree(f"./app/users/user{db_user.id}")
    db.delete(db_user)
    db.commit()
    return None

def upload_file_db(db: Session, file: FileOut):
    db_file = FileDB(user_id=file.user_id, path=file.path,
                      start_date=file.start_date, end_date=file.end_date,
                      upload_date=file.upload_date)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_by_date_db(db: Session, user: UserIn, date: date):
    db_user = get_user_by_email(db, user.email)
    return db.query(FileDB).filter(and_(FileDB.user_id == db_user.id,
                                         or_(func.DATE(FileDB.start_date) == date, func.DATE(FileDB.end_date) == date))).all()

def get_last_files_db(db: Session, user: UserIn):
    db_user = get_user_by_email(db, user.email)
    last_date = db.query(FileDB).filter(FileDB.user_id == db_user.id).order_by(FileDB.id.desc()).first().upload_date
    return db.query(FileDB).filter(and_(FileDB.user_id == db_user.id, FileDB.upload_date == last_date)).all()

def delete_file_db(db: Session, user: UserIn, date: date):
    db_user = get_user_by_email(db, user.email)
    user_data = db.query(FileDB).filter(and_(FileDB.user_id == db_user.id,
                                         or_(func.DATE(FileDB.start_date) == date, func.DATE(FileDB.end_date) == date))).first()
    os.remove(user_data.path) 
    db.delete(user_data)
    db.commit()
    return None

#Endpoints
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

@api.put("/users/", response_model=UserOut)
def update_user_email(new_email: EmailStr, user: UserIn, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    input_data_error(db_user, user)
    return update_user_email_db(db, user.email, new_email)
    
@api.delete("/users/")
def delete_user(user: UserIn, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    input_data_error(db_user, user)
    return delete_user_db(db, user)
    
#Работа с файлами    
@api.post("/files/")
def upload_file(emailIn: EmailStr, passwordIn: str, startDate: datetime, endDate: datetime,
                 up_file: UploadFile, db: Session = Depends(get_db)):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, email=user.email)
    if db_user is None:
        db_user = create_user(user, db)
    elif (user.password + "notreallyhashed" != db_user.hashed_password):
        raise HTTPException(status_code=400, detail="The password was entered incorrectly")

    #сохраняем файл
    directory = f"./app/users/user{db_user.id}"
    f = open(directory+f"/{up_file.filename}", 'wb')
    f.write(up_file.file.read())
    f.close()

    now_date = datetime.now()
    fileOut = FileOut(user_id=db_user.id,path=directory+f"/{up_file.filename}", start_date=startDate,
                      end_date=endDate, upload_date=now_date)
    
    return upload_file_db(db, fileOut)

@api.get("/files/last")
def get_last_files(emailIn: EmailStr, passwordIn: str, db: Session = Depends(get_db)):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, user.email)
    input_data_error(db_user, user)
    return get_last_files_db(db, user)
    
@api.get("/files/")
def get_by_date(emailIn: EmailStr, passwordIn: str, date: date, db: Session = Depends(get_db)):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, user.email)
    input_data_error(db_user, user)
    return get_by_date_db(db, user, date)
    
@api.delete("/files/")
def delete_file(user: UserIn, date: date, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    input_data_error(db_user, user)
    return delete_file_db(db, user, date)

#uvicorn app.db_wiring:api --reload --port 8083
