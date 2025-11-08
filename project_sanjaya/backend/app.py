import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import auth, models, schemas, utils, aviation
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to Project Sanjaya API"}

import random

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db), current_admin: models.User = Depends(auth.get_current_admin_user)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        if user.role == "child":
            user.username = f"{user.username}_{random.randint(1000, 9999)}"
        else:
            raise HTTPException(status_code=400, detail="Username already registered")

    new_user = auth.register_user(db=db, username=user.username, password=user.password, role=user.role)
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    access_token = auth.login_user(db=db, username=form_data.username, password=form_data.password)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/start_trip")
def start_trip(trip: schemas.TripCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    user = db.query(models.User).filter(models.User.username == trip.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session_hash = utils.generate_session_hash(trip.username)
    new_trip = models.Trip(user_id=user.id, session_hash=session_hash, mode=trip.mode)
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    if trip.details:
        for key, value in trip.details.items():
            trip_detail = models.TripDetail(trip_id=new_trip.id, detail_type=key, value=str(value))
            db.add(trip_detail)
        db.commit()

    if new_trip.mode == 'flight' and 'flight_iata' in trip.details:
        # These would be fetched from the flight data or provided by the user
        dep_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        arr_time = dep_time + datetime.timedelta(hours=2)
        aviation.schedule_inflight_checks(db, new_trip.id, trip.details['flight_iata'], dep_time, arr_time)

    return {"session_hash": session_hash}

@app.post("/update_location")
def update_location(location: schemas.LocationUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    trip = db.query(models.Trip).filter(models.Trip.session_hash == location.session_hash).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this trip")

    new_location = models.Location(
        trip_id=trip.id,
        latitude=location.lat,
        longitude=location.lon,
        battery=location.battery,
        timestamp=location.timestamp or datetime.datetime.utcnow()
    )
    db.add(new_location)
    db.commit()
    return {"status": "success"}

@app.post("/sync_data")
def sync_data(sync_data: schemas.SyncData, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    trip = db.query(models.Trip).filter(models.Trip.session_hash == sync_data.session_hash).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to sync data for this trip")

    for point in sync_data.points:
        new_location = models.Location(
            trip_id=trip.id,
            latitude=point.lat,
            longitude=point.lon,
            battery=point.battery,
            timestamp=point.timestamp or datetime.datetime.utcnow()
        )
        db.add(new_location)

    db.commit()
    return {"status": "success", "synced_points": len(sync_data.points)}

@app.get("/users", response_model=list[schemas.User])
def list_users(role: str = None, db: Session = Depends(get_db), current_admin: models.User = Depends(auth.get_current_admin_user)):
    if role:
        users = db.query(models.User).filter(models.User.role == role).all()
    else:
        users = db.query(models.User).all()
    return users

@app.post("/link-parent-child")
def link_parent_child(link: schemas.ParentChildLink, db: Session = Depends(get_db), current_admin: models.User = Depends(auth.get_current_admin_user)):
    parent = db.query(models.User).filter(models.User.username == link.parent_username).first()
    child = db.query(models.User).filter(models.User.username == link.child_username).first()

    if not parent or not child:
        raise HTTPException(status_code=404, detail="Parent or child not found")

    if parent.role != 'parent' or child.role != 'child':
        raise HTTPException(status_code=400, detail="Invalid roles for parent or child")

    # Enforce relationship constraints
    if len(parent.children) >= 2:
        raise HTTPException(status_code=400, detail="Parent already has 2 children")
    if len(child.parents) >= 2:
        raise HTTPException(status_code=400, detail="Child already has 2 parents")

    parent_child_link = models.ParentChild(parent_id=parent.id, child_id=child.id)
    db.add(parent_child_link)
    db.commit()
    return {"status": "success", "message": "Parent and child linked successfully"}

@app.get("/linked-children", response_model=list[schemas.User])
def get_linked_children(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != 'parent':
        raise HTTPException(status_code=403, detail="Only parents can view linked children")

    linked_children = db.query(models.User).join(models.ParentChild, models.User.id == models.ParentChild.child_id).filter(models.ParentChild.parent_id == current_user.id).all()
    return linked_children

@app.post("/heartbeat")
def heartbeat(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    current_user.last_seen = datetime.datetime.utcnow()
    db.commit()
    return {"status": "success"}

@app.get("/child-status/{username}", response_model=schemas.ChildStatus)
def get_child_status(username: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role != 'parent':
        raise HTTPException(status_code=403, detail="Only parents can view child status")

    child = db.query(models.User).filter(models.User.username == username).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Check if the current user is a parent of the child
    link = db.query(models.ParentChild).filter(models.ParentChild.parent_id == current_user.id, models.ParentChild.child_id == child.id).first()
    if not link:
        raise HTTPException(status_code=403, detail="Not authorized to view this child's status")

    latest_location = db.query(models.Location).join(models.Trip).filter(models.Trip.user_id == child.id).order_by(models.Location.timestamp.desc()).first()

    connection_status = "online" if (datetime.datetime.utcnow() - child.last_seen).total_seconds() < 60 else "offline"

    return schemas.ChildStatus(
        username=child.username,
        last_seen=child.last_seen,
        latitude=latest_location.latitude if latest_location else None,
        longitude=latest_location.longitude if latest_location else None,
        battery=latest_location.battery if latest_location else None,
        connection_status=connection_status
    )
