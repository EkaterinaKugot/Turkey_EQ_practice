from pydantic import EmailStr
from fastapi import FastAPI, Depends, HTTPException, UploadFile
from loguru import logger
import uvicorn
from datetime import datetime, date
from sqlalchemy.orm import Session
import os
import shutil
import zipfile

from .database.crud import *
from .database.schemas import *
from .database.models import *


api = FastAPI()
#uvicorn app.main:api --reload --port 8083

logger.add("./app/logs/info.log", level="INFO", retention="1 week")

def input_data_error(db_user: UserDB, user: UserIn):
    if db_user is None:
        logger.info("This email does not exist")
        raise HTTPException(status_code=400, detail="This email does not exist")
    elif user.password + "notreallyhashed" != db_user.hashed_password:
        logger.info(f"{db_user.id} The password was entered incorrectly")
        raise HTTPException(
            status_code=400, detail="The password was entered incorrectly"
        )

def upload_files_archives(db_user: UserDB, up_file: UploadFile):
    directory = user_dir.user_dir + str(db_user.id)

    # сохранение файлов
    file_name = up_file.filename
    f = open(directory + f"/{file_name}", "wb")
    f.write(up_file.file.read())
    f.close()

    logger.info(f"{db_user.id} The file has been uploaded successfully")

    if file_name.split(".")[-1] == "zip":
        with zipfile.ZipFile(directory + f"/{file_name}", "r") as zip_ref:
            uploaded_files = [x for x in zip_ref.namelist() if not x.endswith("/")]           
            dirs = [x for x in zip_ref.namelist() if x.endswith("/")]
            zip_ref.extractall(directory)
        for i in range(len(uploaded_files)):
            uploaded_files[i] = uploaded_files[i].split("/")[-1]       
        if len(dirs) != 0:        
            for file in os.listdir(directory + f"/{dirs[0]}"):
                # Если такой файл существует, то старый файл удалится и заменится новым              
                if os.path.exists(directory + f"/{file}"):
                    os.remove(os.path.join(directory, file))
                shutil.move(directory + f"/{dirs[0]}/{file}", directory)
            
            os.rmdir(os.path.join(directory, dirs[0]))
        os.remove(os.path.join(directory, file_name))
        logger.info(f"{db_user.id} The archive has been successfully unzipped")
    else:
        uploaded_files = [file_name]
    return uploaded_files

# Endpoints
@api.post("/users/", response_model=UserOut)
def create_user(user: UserIn, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        logger.info("Email already registered")
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = create_user_db(db=db, user=user)
    directory = user_dir.user_dir + str(db_user.id)
    if not os.path.exists(directory):     
        os.mkdir(directory)
        logger.info(f"{db_user.id} The user's directory has been created")
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

# Работа с файлами
@api.post("/files/")
def upload_file(
    emailIn: EmailStr,
    passwordIn: str,
    startDate: datetime,
    endDate: datetime,
    up_file: UploadFile,
    db: Session = Depends(get_db),
):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, email=user.email)
    if db_user is None:
        db_user = create_user(user, db)
    elif user.password + "notreallyhashed" != db_user.hashed_password:
        logger.info(f"{db_user.id} The password was entered incorrectly")
        raise HTTPException(
            status_code=400, detail="The password was entered incorrectly"
        )

    directory = user_dir.user_dir + str(db_user.id)
    uploaded_files = upload_files_archives(db_user, up_file)

    for path in uploaded_files:
        delete_file_by_path(db, user, directory + f"/{path}")

    now_date = datetime.now()
    for file in uploaded_files:
        fileOut = FileOut(
            user_id=db_user.id,
            path=directory + f"/{file}",
            start_date=startDate,
            end_date=endDate,
            upload_date=now_date,
        )
        upload_file_db(db, fileOut)

    return uploaded_files


@api.get("/files/last")
def get_last_files(emailIn: EmailStr, passwordIn: str, db: Session = Depends(get_db)):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, user.email)
    input_data_error(db_user, user)
    return get_last_files_db(db, user)


@api.get("/files/")
def get_by_date(
    emailIn: EmailStr, passwordIn: str, date: date, db: Session = Depends(get_db)
):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, user.email)
    input_data_error(db_user, user)
    return get_by_date_db(db, user, date)


@api.delete("/files/")
def delete_file(user: UserIn, date: date, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    input_data_error(db_user, user)
    return delete_file_db(db, user, date)


def main():
    uvicorn.run(f"{os.path.basename(__file__)[:-3]}:api", log_level="info")

if __name__ == '__main__':
    main()
