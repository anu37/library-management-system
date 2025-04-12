from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from .auth_api import router as auth_router

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


app = FastAPI()
app.include_router(auth_router)

@app.get("/")
async def root(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"message": "Hello World"}