from pydantic import EmailStr
from fastapi import FastAPI

api = FastAPI()

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
