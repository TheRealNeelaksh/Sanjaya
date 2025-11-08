from pydantic import BaseModel
from typing import List, Optional
import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TripCreate(BaseModel):
    username: str
    mode: str
    details: Optional[dict] = {}

class LocationUpdate(BaseModel):
    session_hash: str
    lat: float
    lon: float
    battery: Optional[float] = None
    timestamp: Optional[datetime.datetime] = None

class User(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True

class ParentChildLink(BaseModel):
    parent_username: str
    child_username: str

class ChildStatus(BaseModel):
    username: str
    last_seen: datetime.datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    battery: Optional[float] = None
    connection_status: str

class SyncData(BaseModel):
    session_hash: str
    points: List[LocationUpdate]
