from pydantic import EmailStr, BaseModel
from fastapi import FastAPI
import uvicorn
import os
api = FastAPI()

@api.get("/")
async def index():
    return {'message': 'hello everyone'}

@api.get('/hello')
async def index(user_name: str | None = None):
    if user_name :
        return {'message': f'hello {user_name}'}
    else:
        return {'message': 'hello anonymous'}

@api.post('/create_user')
async def create_user(user_name: str, user_mail: EmailStr):
    return {'user_name': user_name, 'user_mail': user_mail}

class UserOut(BaseModel):
    email: EmailStr

class UserIn(UserOut):
    password: str

@api.post("/create_user_from_model", response_model=UserOut)
async def create_user_from_model(user: UserIn):
     return user


def main():
    uvicorn.run(f"{os.path.basename(__file__)[:-3]}:api", log_level="info")

if __name__ == '__main__':
    main()