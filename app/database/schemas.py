from pydantic import EmailStr, BaseModel
from datetime import datetime

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
    start_date: datetime
    end_date: datetime
    upload_date: datetime
    type: str
    epc_date: datetime
    epc_lat: float
    epc_lon: float

class MapIn(BaseModel):
    files: list[str] = ["roti_10_24.h5", "dtec_2_10_10_24.h5"]
    date: list[datetime] = ["2023-02-06T10:25:00.000Z", "2023-02-06T10:40:00.000Z"]
    lat: list[int] = [25, 50]
    lon: list[int] = [25, 50]
    c_limits: list[list[float]] = [[ -0.1, 0.3 ]]

class DistanceTime(BaseModel):
    file: str = "roti_10_24.h5"
    direction: str = "all"
    c_limits: list[float] = [0, 0.5]
    velocity: list[float] = [2]
    start: list[datetime] = ["2023-02-06 10:35:00"]
    style: list[str] = ["solid"]

class SupportPlot(BaseModel):
    file: str = "tnpgn_2023-02-06.h5"
    sites: list[str] = ['anmu', 'fini', 'mrsi', 'silf', 'kamn', 'sarv', 'aksi',
         'alny', 'lefk', 'mgos', 'bcak', 'antl', 'cav2', 'elmi',
         'kaas', 'feth', 'mug1', 'slee', 'istn', 'karb', 'ylov',
         'boyt', 'sary', 'slvr', 'vezi', 'tekr', 'kstm', 'cank',
         'kuru', 'cmld', 'zong']
    span: list[str] = ["2023-02-06 10:00:00", "2023-02-06 11:00:00"]
    sat: str = 'G17'

