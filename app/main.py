from pydantic import EmailStr
from fastapi import FastAPI, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
import io
import uvicorn
from datetime import datetime, date
from sqlalchemy.orm import Session
import os
import shutil
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from turkey_eq.turkey import *

from .database.crud import *
from .database.schemas import *
from .database.models import *

api = FastAPI()
# uvicorn app.main:api --reload --port 8083

logger.add("./app/logs/info.log", level="INFO", rotation="100 KB", compression="zip")
logger.add("./app/logs/error.log", level="ERROR", rotation="100 KB", compression="zip")

class Image_dir():
    image_dir = './app/images/user'
    img_dir = "./app/images"

image_dir = Image_dir()

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

def data_for_drawing_maps(userId: int, mapFiles: MapIn, db: Session = Depends(get_db)):

    FILES = {}
    C_LIMITS = {}
    EPICENTERS = {'lat': 0, 'lon': 0, 'time': datetime(2023, 2, 6, 10, 24, 50)}

    for file in mapFiles.files:
        file = get_data_about_file(db, file, userId)
        if not file:
            logger.error(f"{userId} This file has not been uploaded")
            raise HTTPException(status_code=400, detail="This file has not been uploaded")
        if file.type in list(C_LIMITS.keys()):
            logger.error(f"{userId} These files are of the same type")
            raise HTTPException(status_code=400, detail="These files are of the same type")
        else:
            if len(list(FILES.keys())) == 0:
                EPICENTERS['lat'] = file.epc_lat
                EPICENTERS['lon'] = file.epc_lon
                EPICENTERS['time'] = file.epc_date
            else:
                if EPICENTERS['lat'] != file.epc_lat or EPICENTERS['lon'] != file.epc_lon or \
                        EPICENTERS['time'] != file.epc_date:
                    logger.error(f"{userId} These files must contain different data about the epicenter")
                    raise HTTPException(status_code=400,
                                        detail="These files must contain different data about the epicenter")
            C_LIMITS[file.type] = []
            if file.path not in list(FILES.keys()):
                FILES[file.path] = file.type
            else:
                logger.error(f"{userId} The same files were selected")
                raise HTTPException(status_code=400, detail="The same files were selected")

    if len(mapFiles.files) != len(mapFiles.c_limits) and len(mapFiles.c_limits) != 1:
        logger.error(f"{userId} Incorrect number of elements in the color range")
        raise HTTPException(status_code=400, detail="Incorrect number of elements in the color range")

    mapFiles.lon = checking_ranges(mapFiles.lon, userId)
    mapFiles.lat = checking_ranges(mapFiles.lat, userId)

    for c_limit in range(len(mapFiles.c_limits)):
        mapFiles.c_limits[c_limit] = checking_ranges(mapFiles.c_limits[c_limit], userId)

    if len(mapFiles.c_limits) == 1:
        for key in list(C_LIMITS.keys()):
            C_LIMITS[key] = mapFiles.c_limits[0] + ['TECu']
    else:
        keys = list(C_LIMITS.keys())
        for c_limit in range(len(mapFiles.c_limits)):
            C_LIMITS[keys[c_limit]] = mapFiles.c_limits[c_limit] + ['TECu']

    return C_LIMITS, FILES, EPICENTERS

def checking_ranges(rangers, userId: int):
    if len(rangers) != 2:
        logger.error(f"{userId} The number of elements in the color scale is not equal to two")
        raise HTTPException(status_code=400, detail="The number of elements in the color scale is not equal to two")

    if rangers[0] == rangers[1]:
        raise HTTPException(status_code=400, detail="The value is not a diagnosis")

    if rangers[1] < rangers[0]:
        range = rangers[1]
        rangers[1] = rangers[0]
        rangers[0] = range

    return rangers

def zipfiles(path):
    file_list = os.listdir(path)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for file in file_list:
            file_path = os.path.join(path, file)
            zip_file.write(file_path, file)

    buffer.seek(0)

    response = StreamingResponse(buffer, media_type="application/zip")
    response.headers["Content-Disposition"] = "attachment; filename=archive.zip"
    return response

def data_for_distance_time(userId: int, distanceTime: DistanceTime, db: Session = Depends(get_db)):
    file = get_data_about_file(db, distanceTime.file, userId)
    if not file:
        logger.error(f"{userId} This file has not been uploaded")
        raise HTTPException(status_code=400, detail="This file has not been uploaded")
    else:
        FILE = {file.path: file.type}

    if not (distanceTime.direction in ["all", "north", "south", "east", "west"]):
        logger.error(f"{userId} This direction does not exist")
        raise HTTPException(status_code=400, detail="This direction does not exist")
    
    if len(distanceTime.c_limits) != 2:
        logger.error(f"{userId} Incorrect number of elements in the color range")
        raise HTTPException(status_code=400, detail="Incorrect number of elements in the color range")
    else:
        if distanceTime.c_limits[0] > distanceTime.c_limits[1]:
            t = distanceTime.c_limits[1]
            distanceTime.c_limits[1] = distanceTime.c_limits[0]
            distanceTime.c_limits[0] = t
        C_LIMITS = {file.type: [distanceTime.c_limits[0], distanceTime.c_limits[1], "TECu"]}

    EPICENTER = {'lat': file.epc_lat, 'lon': file.epc_lon, 'time': file.epc_date}

    return C_LIMITS, FILE, EPICENTER

def create_images_dir(path: str):
    if not os.path.exists(image_dir.img_dir):
        os.makedirs(image_dir.img_dir)
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            os.remove(file_path)


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
    if os.path.exists(f"{image_dir.image_dir}{db_user.id}"):
        shutil.rmtree(f"{image_dir.image_dir}{db_user.id}")
        logger.info(f"{db_user.id} Maps successfully deleted")
    return delete_user_db(db, user)


# Работа с файлами
@api.post("/files/")
def upload_file(
    emailIn: EmailStr,
    passwordIn: str,
    startDate: datetime,
    endDate: datetime,
    type: str,
    epc_date: datetime,
    epc_lat: float,
    epc_lon: float,
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
            type=type,
            epc_date=epc_date,
            epc_lat=epc_lat,
            epc_lon=epc_lon
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

@api.post("/map/")
def draw_map(emailIn: EmailStr, passwordIn: str, mapFiles: MapIn, db: Session = Depends(get_db)):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, user.email)
    input_data_error(db_user, user)

    if len(mapFiles.date) > 3 or len(mapFiles.date) < 1:
        logger.error(f"{db_user.id} The number of dates is incorrect")
        raise HTTPException(status_code=400, detail="The number of dates is incorrect")
    
    C_LIMITS, FILES, EPICENTERS = data_for_drawing_maps(db_user.id, mapFiles, db)
    path = f"{image_dir.image_dir}{db_user.id}"

    create_images_dir(path)

    plot_maps([FILES],
              FILES,
              EPICENTERS,
              clims=C_LIMITS,
              times=mapFiles.date,
              lat_limits=mapFiles.lat,
              lon_limits=mapFiles.lon,
              nrows=1,
              ncols=len(mapFiles.date),
              savefig=f"{path}/map")
    
    logger.info(f"{db_user.id} The maps have been successfully generated")

    return zipfiles(path)


@api.post("/distance-time/")
def draw_distance_time(emailIn: EmailStr, passwordIn: str, distanceTime: DistanceTime, db: Session = Depends(get_db)):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, user.email)
    input_data_error(db_user, user)

    if len(distanceTime.velocity) != len(distanceTime.start) or \
        len(distanceTime.start) != len(distanceTime.style):
        logger.error(f"{db_user.id} You need the same number of elements in velocity, start and style")
        raise HTTPException(status_code=400, detail="You need the same number of elements in velocity, start and style")
    elif len(distanceTime.style) != 0:
        for i in distanceTime.style:
            if not(i in ["solid", "dashed", "dashdot", "dotted"]):
                logger.error(f"{db_user.id} There is no such line style")
                raise HTTPException(status_code=400, detail="There is no such line style")

    C_LIMITS, FILE, EPICENTER = data_for_distance_time(db_user.id, distanceTime, db)

    data = []
    type1 = ""
    for i, j in FILE.items():
        data = retrieve_data(i, j)
        type1 = j
    x, y, c = get_dist_time(data, EPICENTER, distanceTime.direction)
    plot_distance_time(x, y, c, type1, EPICENTER, clims=C_LIMITS, data=data)

    if len(distanceTime.velocity) != 0:
        for vel, start, style in zip(distanceTime.velocity, distanceTime.start, distanceTime.style):
            plot_line(vel, start, style)

    path = f"{image_dir.image_dir}{db_user.id}"
    create_images_dir(path)    
    plt.savefig(f"{path}/chart.jpg")

    logger.info(f"{db_user.id} Distance-time diagram successfully generated")

    return zipfiles(path)

@api.post("/support-plot/")
def draw_support_plot(emailIn: EmailStr, passwordIn: str, supportPlot: SupportPlot, db: Session = Depends(get_db)):
    user = UserIn(email=emailIn, password=passwordIn)
    db_user = get_user_by_email(db, user.email)
    input_data_error(db_user, user)

    file = get_data_about_file(db, supportPlot.file, db_user.id)
    if not file:
        logger.error(f"{db_user.id} This file has not been uploaded")
        raise HTTPException(status_code=400, detail="This file has not been uploaded")
    
    EPICENTER = {'lat': file.epc_lat, 'lon': file.epc_lon, 'time': file.epc_date}

    plot_sites(file.path, supportPlot.sat, supportPlot.sites[:], file.type, EPICENTER, supportPlot.span)

    path = f"{image_dir.image_dir}{db_user.id}"
    create_images_dir(path)  
    plt.savefig(f"{path}/plot.jpg")

    logger.info(f"{db_user.id} Support plot successfully generated")

    return zipfiles(path)


def main():
    uvicorn.run(f"{os.path.basename(__file__)[:-3]}:api", log_level="info")


if __name__ == '__main__':
    main()
