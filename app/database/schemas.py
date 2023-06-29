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
    files: list[str]
    date: list[datetime]
    lat: list[int]
    lon: list[int]
