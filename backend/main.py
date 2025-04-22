from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import databases
import sqlalchemy
from fastapi.middleware.cors import CORSMiddleware

# Database configuration
DATABASE_URL = "sqlite:///./identity_verification.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Define tables
users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(100)),
    sqlalchemy.Column("cnic", sqlalchemy.String(15), unique=True),
    sqlalchemy.Column("phone", sqlalchemy.String(15)),
    sqlalchemy.Column("email", sqlalchemy.String(100)),
)

verification_requests = sqlalchemy.Table(
    "verification_requests",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("request_date", sqlalchemy.DateTime),
    sqlalchemy.Column("status", sqlalchemy.String(20)),
    sqlalchemy.Column("verification_method", sqlalchemy.String(50)),
    sqlalchemy.Column("verified_by", sqlalchemy.String(100)),
)

# Create the database
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

# Models
class User(BaseModel):
    name: str
    cnic: str
    phone: str
    email: str

class UserInDB(User):
    id: int

class VerificationRequest(BaseModel):
    user_id: int
    status: str
    verification_method: str
    verified_by: str

class VerificationRequestInDB(VerificationRequest):
    id: int
    request_date: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# FastAPI app
app = FastAPI(title="PakID Identity Verification API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup():
    await database.connect()

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Routes for Users
@app.post("/users/", response_model=UserInDB)
async def create_user(user: User):
    query = users.insert().values(**user.dict())
    last_record_id = await database.execute(query)
    return {**user.dict(), "id": last_record_id}

@app.get("/users/", response_model=List[UserInDB])
async def read_users():
    query = users.select()
    return await database.fetch_all(query)

@app.get("/users/{user_id}", response_model=UserInDB)
async def read_user(user_id: int):
    query = users.select().where(users.c.id == user_id)
    user = await database.fetch_one(query)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserInDB)
async def update_user(user_id: int, user: User):
    query = users.update().where(users.c.id == user_id).values(**user.dict())
    await database.execute(query)
    return {**user.dict(), "id": user_id}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    return {"message": "User deleted successfully"}

# Routes for Verification Requests
@app.post("/verifications/", response_model=VerificationRequestInDB)
async def create_verification(request: VerificationRequest):
    current_time = datetime.utcnow()
    query = verification_requests.insert().values(
        user_id=request.user_id,
        status=request.status,
        verification_method=request.verification_method,
        verified_by=request.verified_by,
        request_date=current_time
    )
    last_record_id = await database.execute(query)
    return {**request.dict(), "id": last_record_id, "request_date": current_time}

@app.get("/verifications/", response_model=List[VerificationRequestInDB])
async def read_verifications():
    query = verification_requests.select()
    return await database.fetch_all(query)

@app.get("/verifications/{verification_id}", response_model=VerificationRequestInDB)
async def read_verification(verification_id: int):
    query = verification_requests.select().where(verification_requests.c.id == verification_id)
    verification = await database.fetch_one(query)
    if verification is None:
        raise HTTPException(status_code=404, detail="Verification request not found")
    return verification

@app.put("/verifications/{verification_id}", response_model=VerificationRequestInDB)
async def update_verification(verification_id: int, request: VerificationRequest):
    query = verification_requests.update().where(verification_requests.c.id == verification_id).values(
        user_id=request.user_id,
        status=request.status,
        verification_method=request.verification_method,
        verified_by=request.verified_by
    )
    await database.execute(query)
    return {**request.dict(), "id": verification_id}

@app.delete("/verifications/{verification_id}")
async def delete_verification(verification_id: int):
    query = verification_requests.delete().where(verification_requests.c.id == verification_id)
    await database.execute(query)
    return {"message": "Verification request deleted successfully"}