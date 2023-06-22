from pydantic import EmailStr, BaseModel
from fastapi import FastAPI, Depends, HTTPException, UploadFile
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
<<<<<<< Updated upstream
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
=======
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
=======
    start_date: str
    end_date: str
    upload_date: str

>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
=======
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    upload_date = Column(DateTime, nullable=False)
>>>>>>> Stashed changes
    user = relationship("UserDB", back_populates="files")
    
Base.metadata.create_all(bind=engine)

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
def upload_file(emailIn: EmailStr, passwordIn: str, up_file: UploadFile, dirname: str,  db: Session = Depends(get_db)):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, email=user.email)
    if db_user is None:
        db_user = create_user(user, db)
    elif (user.password + "notreallyhashed" != db_user.hashed_password):
        raise HTTPException(status_code=400, detail="The password was entered incorrectly")

    directory = f"./app/users/user{db_user.id}/{dirname}"
    if not os.path.exists(directory):
        os.mkdir(directory)

    #сохраняем файл
    f = open(directory+f"/{up_file.filename}", 'wb')
    f.write(up_file.file.read())
    f.close()

    fileOut = FileOut(user_id=db_user.id,path=directory+f"/{up_file.filename}")
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


