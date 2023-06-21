from pydantic import EmailStr, BaseModel
from fastapi import FastAPI, Depends, HTTPException
from fastapi import UploadFile, File

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

api = FastAPI()

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_DB.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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

class fileIn(BaseModel):
    email: EmailStr
    password: str
    file_name: str

#Model DB
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class FilesDB(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file = Column(String)
    
Base.metadata.create_all(bind=engine)

#CRUD
def create_user_db(db: Session, user: UserIn):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = UserDB(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_file_db(db: Session, data: fileIn):
    user_id = 1
    db_file = FilesDB(user_id=user_id, file=data.file_name)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_user_by_email(db: Session, email: str):
    return db.query(UserDB).filter(UserDB.email == email).first()

#Endpoints
@api.post("/users/", response_model=UserOut)
def create_user(user: UserIn, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user_db(db=db, user=user)

@api.post("/files/")
def create_dir(data: fileIn, db: Session = Depends(get_db)):
    return create_file_db(db=db, data=data)

#newtext

@api.post("/file/upload-file")
def upload_file(file: UploadFile):
    f = open(file.filename, 'w')
    f.write(str(file.file.read()))
    f.close()
    return {'file': 'uploaded'}


