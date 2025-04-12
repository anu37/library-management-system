from fastapi import FastAPI
from database import engine, Base

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}