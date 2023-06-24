from .models import *
from .schemas import *
from datetime import date
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session
import shutil
import os


class User_dir():
    user_dir = "./app/users/user"

user_dir = User_dir()


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
    user_data = db.query(FileDB).filter(FileDB.user_id == db_user.id).all()
    for data in user_data:
        db.delete(data)
    shutil.rmtree(user_dir.user_dir + str(db_user.id))
    db.delete(db_user)
    db.commit()
    return None


def upload_file_db(db: Session, file: FileOut):
    db_file = FileDB(
        user_id=file.user_id,
        path=file.path,
        start_date=file.start_date,
        end_date=file.end_date,
        upload_date=file.upload_date,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_by_date_db(db: Session, user: UserIn, date: date):
    db_user = get_user_by_email(db, user.email)
    return (
        db.query(FileDB)
        .filter(
            and_(
                FileDB.user_id == db_user.id,
                or_(
                    func.DATE(FileDB.start_date) == date,
                    func.DATE(FileDB.end_date) == date,
                ),
            )
        )
        .all()
    )


def get_last_files_db(db: Session, user: UserIn):
    db_user = get_user_by_email(db, user.email)
    last_date = (
        db.query(FileDB)
        .filter(FileDB.user_id == db_user.id)
        .order_by(FileDB.id.desc())
        .first()
        .upload_date
    )
    return (
        db.query(FileDB)
        .filter(and_(FileDB.user_id == db_user.id, FileDB.upload_date == last_date))
        .all()
    )


def delete_file_db(db: Session, user: UserIn, date: date):
    db_user = get_user_by_email(db, user.email)
    user_data = (
        db.query(FileDB)
        .filter(
            and_(
                FileDB.user_id == db_user.id,
                or_(
                    func.DATE(FileDB.start_date) == date,
                    func.DATE(FileDB.end_date) == date,
                ),
            )
        )
        .all()
    )
    for data in user_data:
        os.remove(data.path)
        db.delete(data)
    db.commit()
    return None

def delete_file_by_path(db: Session, user: UserIn, path: str):
    db_user = get_user_by_email(db, email=user.email)
    user_data = (
        db.query(FileDB)
        .filter(
            and_(
                FileDB.user_id == db_user.id,
                FileDB.path == path
            )
        )
        .first()
    )
    if not(user_data is None):
        db.delete(user_data)
        db.commit()
    return None