from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from src import auth_api
from src import books_api
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()
app.state.limiter = Limiter

# Set up the rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_api.router)
app.include_router(books_api.router)

@app.get("/")
async def root(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"message": "Hello World"}