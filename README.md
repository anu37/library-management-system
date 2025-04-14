# Library Management System 

### Stack:
FastAPI |
PostgresSQL |
Docker |

This repo includes the API for managing library systems such as book anagement, user management, borrow history, Authentication using JWT token. 

## Set up instructions

#### 1. Clone the repo 

```
git clone 
cd library-management-system
```
#### 2. Create a Virtual environment and install dependencies

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Set environment variables

Create a `.env` file in the root directory:

```
SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/library_db
```

####  4. Run the application

```
uvicorn src.main:app --reload
```

[http://localhost:8000/docs](http://localhost:8000/docs) for Swagger UI.



## Database Setup & Migrations

#### Initialize Alembic

```
alembic init alembic
```

#### Generate a migration

```
alembic revision --autogenerate -m "Initial migration"
```

#### Apply migrations

```
alembic upgrade head
```

## Docker Setup

```
docker build -t library-system .
docker run -d -p 8000:8000 library-system
```

