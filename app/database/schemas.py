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

class MapIn(BaseModel):
    files: list[str]
    date: list[datetime]
    lat: list[int]
    lon: list[int]
