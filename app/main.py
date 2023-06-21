from pydantic import EmailStr, BaseModel
from fastapi import FastAPI

api = FastAPI()

class UserBase(BaseModel):
    name:str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    pass

class UserIn(BaseModel):
    password: str

@api.get("/")
async def index():
    return {'message': 'hello everyone'}

@api.get('/hello')
async def index(user_name: str | None = None):
    if user_name :
        return {'message': f'hello {user_name}'}
    return {'message': 'hello anonymous'}

@api.post('/create_user')
async def create_user(user_name: str, user_mail: EmailStr):
    return {'user_name': user_name, 'user_mail': user_mail}

@api.post("/create_user_from_model", response_model=UserOut)
async def create_user_from_model(user: UserBase):
     return user
