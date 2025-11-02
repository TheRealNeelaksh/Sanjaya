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

class SyncData(BaseModel):
    session_hash: str
    points: List[LocationUpdate]
