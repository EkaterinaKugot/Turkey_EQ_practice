from .models import *
from .schemas import *
from datetime import date
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session
import shutil
import os
from loguru import logger


class User_dir():
    user_dir = "./app/users/user"

user_dir = User_dir()

logger.add("./app/logs/error.log", level="ERROR", retention="1 week")

# CRUD
def create_user_db(db: Session, user: UserIn):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = UserDB(email=user.email, hashed_password=fake_hashed_password)
    try:
        db.add(db_user)
    except:
        return logger.error("Failed to create a new user")
    db.commit()
    db.refresh(db_user)
    logger.info(f"{db_user.id} The user has been successfully created")
    return db_user


def get_user_by_email(db: Session, email: str):
    try:
        db_user = db.query(UserDB).filter(UserDB.email == email).first()
    except:
        return logger.error("Error receiving user data by email")
    return db_user


def update_user_email_db(db: Session, email: str, new_email: str):
    db_user = get_user_by_email(db, email)
    db_user.email = new_email
    db.commit()
    logger.info(f"{db_user.id} The user has successfully updated the email")
    return db_user


def delete_user_db(db: Session, user: UserIn):
    db_user = get_user_by_email(db, user.email)
    try:
        user_data = db.query(FileDB).filter(FileDB.user_id == db_user.id).all()
    except:
        return logger.error("Error getting data about user files by id")
    for data in user_data:
        db.delete(data)
    shutil.rmtree(user_dir.user_dir + str(db_user.id))
    db.delete(db_user)
    db.commit()
    logger.info(f"{db_user.id} The user and his files have been successfully deleted")
    return None


def upload_file_db(db: Session, file: FileOut):
    db_file = FileDB(
        user_id=file.user_id,
        path=file.path,
        start_date=file.start_date,
        end_date=file.end_date,
        upload_date=file.upload_date,
        type=file.type,
        epc_date=file.epc_date,
        epc_lat=file.epc_lat,
        epc_lon=file.epc_lon
    )
    try:
        db.add(db_file)
    except:
        return logger.error(f"{file.user_id} Error adding file data to the database")
    db.commit()
    db.refresh(db_file)
    logger.info(f"{file.user_id} File data has been successfully added to the database")
    return db_file


def get_by_date_db(db: Session, user: UserIn, date: date):
    db_user = get_user_by_email(db, user.email)
    try:
        data = (
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
    except:
        return logger.error(f"{db_user.id} Error getting file data by date")
    logger.info(f"{db_user.id} File data by date successfully received")
    return data


def get_last_files_db(db: Session, user: UserIn):
    db_user = get_user_by_email(db, user.email)
    try:
        last_date = (
            db.query(FileDB)
            .filter(FileDB.user_id == db_user.id)
            .order_by(FileDB.id.desc())
            .first()
            .upload_date
        )
    except:
        return logger.error(f"{db_user.id} Error getting the last upload date")
    try:
        data = (
            db.query(FileDB)
            .filter(and_(FileDB.user_id == db_user.id, FileDB.upload_date == last_date))
            .all()
        )
    except:
        return logger.error(f"{db_user.id} Error getting the latest uploaded files")
    logger.info(f"{db_user.id} File data on the last upload date was successfully received")
    return data


def delete_file_db(db: Session, user: UserIn, date: date):
    db_user = get_user_by_email(db, user.email)
    user_data = get_by_date_db(db, user, date)
    for data in user_data:
        os.remove(data.path)
        db.delete(data)
    db.commit()
    logger.info(f"{db_user.id} Files successfully deleted")
    return None

def delete_file_by_path(db: Session, user: UserIn, path: str):
    db_user = get_user_by_email(db, email=user.email)
    try:
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
    except:
        return logger.error(f"{db_user.id} Error deleting duplicate file data from the database")
    if not(user_data is None):
        db.delete(user_data)
        db.commit()
        logger.info(f"{db_user.id} Duplicate file data has been successfully deleted")
    return None