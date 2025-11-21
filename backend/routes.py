"""
API Routes for Project Sanjaya v2.1
All endpoints for authentication, trip management, and tracking
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import json

from models import (
    User, Trip, TripDetail, Location, Geofence, Alert, ParentChild,
    RoleEnum, TripModeEnum, TripStatusEnum, AlertTypeEnum
)
from auth import (
    register_user, login_user, get_current_user, require_role
)
from utils import (
    generate_session_hash, get_current_place, parse_tracking_id
)

router = APIRouter()


# ============== Pydantic Models ==============

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(child|parent|admin)$")


class LoginRequest(BaseModel):
    username: str
    password: str


class GeofenceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    radius_m: float = Field(..., gt=0)


class TripStart(BaseModel):
    mode: str = Field(..., pattern="^(college|flight|train|road)$")
    details: Optional[dict] = None
    start_place: Optional[str] = None
    end_place: Optional[str] = None


class LocationUpdate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    battery: Optional[int] = Field(None, ge=0, le=100)
    timestamp: datetime


class LocationBatch(BaseModel):
    locations: List[LocationUpdate]


class ParentChildLink(BaseModel):
    parent_username: str
    child_username: str


# ============== Database Dependency ==============

def get_db():
    """Get database session"""
    from app import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============== Authentication Routes ==============

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        role_enum = RoleEnum[request.role]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )
    
    user = register_user(db, request.username, request.password, role_enum)
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.value
        }
    }


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login and receive JWT token"""
    return login_user(db, request.username, request.password)


# ============== Geofence Routes ==============

@router.post("/geofences", status_code=status.HTTP_201_CREATED)
async def create_geofence(
    geofence: GeofenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new geofence for the current user"""
    new_geofence = Geofence(
        user_id=current_user.id,
        name=geofence.name,
        lat=geofence.lat,
        lon=geofence.lon,
        radius_m=geofence.radius_m
    )
    
    db.add(new_geofence)
    db.commit()
    db.refresh(new_geofence)
    
    return {
        "message": "Geofence created",
        "geofence": {
            "id": new_geofence.id,
            "name": new_geofence.name,
            "lat": new_geofence.lat,
            "lon": new_geofence.lon,
            "radius_m": new_geofence.radius_m
        }
    }


@router.get("/geofences")
async def get_geofences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all geofences for current user"""
    geofences = db.query(Geofence).filter(
        Geofence.user_id == current_user.id
    ).all()
    
    return {
        "geofences": [
            {
                "id": g.id,
                "name": g.name,
                "lat": g.lat,
                "lon": g.lon,
                "radius_m": g.radius_m
            }
            for g in geofences
        ]
    }


@router.delete("/geofences/{geofence_id}")
async def delete_geofence(
    geofence_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a geofence"""
    geofence = db.query(Geofence).filter(
        Geofence.id == geofence_id,
        Geofence.user_id == current_user.id
    ).first()
    
    if not geofence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Geofence not found"
        )
    
    db.delete(geofence)
    db.commit()
    
    return {"message": "Geofence deleted"}


# ============== Trip Routes ==============

@router.post("/start_trip", status_code=status.HTTP_201_CREATED)
async def start_trip(
    trip_data: TripStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new trip"""
    # Check if user already has an active trip
    active_trip = db.query(Trip).filter(
        Trip.user_id == current_user.id,
        Trip.status == TripStatusEnum.active
    ).first()
    
    if active_trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active trip. End it before starting a new one."
        )
    
    # Generate session hash
    session_hash = generate_session_hash(current_user.username)
    
    # Create trip
    try:
        mode_enum = TripModeEnum[trip_data.mode]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid trip mode"
        )
    
    new_trip = Trip(
        user_id=current_user.id,
        mode=mode_enum,
        status=TripStatusEnum.active,
        session_hash=session_hash
    )
    
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    
    # Add trip details
    if trip_data.details or trip_data.start_place or trip_data.end_place:
        trip_detail = TripDetail(
            trip_id=new_trip.id,
            details_json=json.dumps(trip_data.details) if trip_data.details else None,
            start_place=trip_data.start_place,
            end_place=trip_data.end_place
        )
        db.add(trip_detail)
        db.commit()
    
    # Create departure alert for parents
    parents = db.query(User).join(
        ParentChild, ParentChild.parent_id == User.id
    ).filter(ParentChild.child_id == current_user.id).all()
    
    for parent in parents:
        alert = Alert(
            user_id=parent.id,
            message=f"{current_user.username} started a {trip_data.mode} trip",
            alert_type=AlertTypeEnum.departure
        )
        db.add(alert)
    
    db.commit()
    
    tracking_link = f"/track/{current_user.username}-{session_hash}"
    
    return {
        "message": "Trip started",
        "trip": {
            "id": new_trip.id,
            "mode": new_trip.mode.value,
            "session_hash": session_hash,
            "tracking_link": tracking_link,
            "start_time": new_trip.start_time.isoformat()
        }
    }


@router.post("/update_location")
async def update_location(
    location_data: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current location for active trip"""
    # Get active trip
    active_trip = db.query(Trip).filter(
        Trip.user_id == current_user.id,
        Trip.status == TripStatusEnum.active
    ).first()
    
    if not active_trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active trip found"
        )
    
    # Add location
    new_location = Location(
        trip_id=active_trip.id,
        lat=location_data.lat,
        lon=location_data.lon,
        battery=location_data.battery,
        timestamp=location_data.timestamp
    )
    
    db.add(new_location)
    
    # Check geofences for alerts
    geofences = db.query(Geofence).filter(
        Geofence.user_id == current_user.id
    ).all()
    
    current_place = get_current_place(location_data.lat, location_data.lon, geofences)
    
    db.commit()
    
    return {
        "message": "Location updated",
        "current_place": current_place
    }


@router.post("/sync_data")
async def sync_data(
    batch: LocationBatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sync batch of cached locations"""
    active_trip = db.query(Trip).filter(
        Trip.user_id == current_user.id,
        Trip.status == TripStatusEnum.active
    ).first()
    
    if not active_trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active trip found"
        )
    
    # Add all locations
    for loc in batch.locations:
        new_location = Location(
            trip_id=active_trip.id,
            lat=loc.lat,
            lon=loc.lon,
            battery=loc.battery,
            timestamp=loc.timestamp
        )
        db.add(new_location)
    
    db.commit()
    
    return {
        "message": f"Synced {len(batch.locations)} locations",
        "count": len(batch.locations)
    }


@router.post("/end_trip")
async def end_trip(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End active trip"""
    active_trip = db.query(Trip).filter(
        Trip.user_id == current_user.id,
        Trip.status == TripStatusEnum.active
    ).first()
    
    if not active_trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active trip found"
        )
    
    active_trip.status = TripStatusEnum.ended
    active_trip.end_time = datetime.utcnow()
    
    # Create arrival alert for parents
    parents = db.query(User).join(
        ParentChild, ParentChild.parent_id == User.id
    ).filter(ParentChild.child_id == current_user.id).all()
    
    for parent in parents:
        alert = Alert(
            user_id=parent.id,
            message=f"{current_user.username} ended their trip",
            alert_type=AlertTypeEnum.arrival
        )
        db.add(alert)
    
    db.commit()
    
    return {"message": "Trip ended successfully"}


@router.get("/my_trips")
async def get_my_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all trips for current user"""
    trips = db.query(Trip).filter(
        Trip.user_id == current_user.id
    ).order_by(Trip.start_time.desc()).all()
    
    return {
        "trips": [
            {
                "id": t.id,
                "mode": t.mode.value,
                "status": t.status.value,
                "start_time": t.start_time.isoformat(),
                "end_time": t.end_time.isoformat() if t.end_time else None
            }
            for t in trips
        ]
    }


# ============== Tracking Route (Public) ==============

@router.get("/track/{tracking_id}")
async def track(tracking_id: str, db: Session = Depends(get_db)):
    """Public tracking endpoint - no authentication required"""
    try:
        username, session_hash = parse_tracking_id(tracking_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tracking ID"
        )
    
    # Find trip
    trip = db.query(Trip).join(User).filter(
        User.username == username,
        Trip.session_hash == session_hash
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Get locations
    locations = db.query(Location).filter(
        Location.trip_id == trip.id
    ).order_by(Location.timestamp.asc()).all()
    
    # Get geofences for place names
    geofences = db.query(Geofence).filter(
        Geofence.user_id == trip.user_id
    ).all()
    
    # Get current place
    current_place = "Unknown"
    if locations:
        last_loc = locations[-1]
        current_place = get_current_place(last_loc.lat, last_loc.lon, geofences)
    
    return {
        "trip": {
            "username": username,
            "mode": trip.mode.value,
            "status": trip.status.value,
            "start_time": trip.start_time.isoformat(),
            "current_place": current_place
        },
        "locations": [
            {
                "lat": loc.lat,
                "lon": loc.lon,
                "battery": loc.battery,
                "timestamp": loc.timestamp.isoformat()
            }
            for loc in locations
        ]
    }


# ============== Parent Routes ==============

@router.post("/link_child")
async def link_child(
    link: ParentChildLink,
    current_user: User = Depends(require_role([RoleEnum.parent, RoleEnum.admin])),
    db: Session = Depends(get_db)
):
    """Link a parent to a child"""
    parent = db.query(User).filter(User.username == link.parent_username).first()
    child = db.query(User).filter(User.username == link.child_username).first()
    
    if not parent or not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if parent.role != RoleEnum.parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent must have parent role"
        )
    
    if child.role != RoleEnum.child:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Child must have child role"
        )
    
    # Check if link exists
    existing = db.query(ParentChild).filter(
        ParentChild.parent_id == parent.id,
        ParentChild.child_id == child.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link already exists"
        )
    
    new_link = ParentChild(parent_id=parent.id, child_id=child.id)
    db.add(new_link)
    db.commit()
    
    return {"message": "Child linked successfully"}


@router.get("/my_children")
async def get_my_children(
    current_user: User = Depends(require_role([RoleEnum.parent])),
    db: Session = Depends(get_db)
):
    """Get all children linked to parent"""
    children = db.query(User).join(
        ParentChild, ParentChild.child_id == User.id
    ).filter(ParentChild.parent_id == current_user.id).all()
    
    result = []
    for child in children:
        # Get active trip
        active_trip = db.query(Trip).filter(
            Trip.user_id == child.id,
            Trip.status == TripStatusEnum.active
        ).first()
        
        child_data = {
            "id": child.id,
            "username": child.username,
            "has_active_trip": active_trip is not None
        }
        
        if active_trip:
            child_data["tracking_link"] = f"/track/{child.username}-{active_trip.session_hash}"
        
        result.append(child_data)
    
    return {"children": result}


# ============== Admin Routes ==============

@router.get("/admin/users")
async def get_all_users(
    current_user: User = Depends(require_role([RoleEnum.admin])),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    users = db.query(User).all()
    
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role.value,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ]
    }


@router.get("/admin/trips")
async def get_all_trips(
    current_user: User = Depends(require_role([RoleEnum.admin])),
    db: Session = Depends(get_db)
):
    """Get all trips (admin only)"""
    trips = db.query(Trip).join(User).all()
    
    return {
        "trips": [
            {
                "id": t.id,
                "username": t.user.username,
                "mode": t.mode.value,
                "status": t.status.value,
                "start_time": t.start_time.isoformat()
            }
            for t in trips
        ]
    }


@router.get("/admin/geofences")
async def get_all_geofences(
    current_user: User = Depends(require_role([RoleEnum.admin])),
    db: Session = Depends(get_db)
):
    """Get all geofences (admin only)"""
    geofences = db.query(Geofence).join(User).all()
    
    return {
        "geofences": [
            {
                "id": g.id,
                "user": g.user.username,
                "name": g.name,
                "lat": g.lat,
                "lon": g.lon,
                "radius_m": g.radius_m
            }
            for g in geofences
        ]
    }