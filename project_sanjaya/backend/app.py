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

@app.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = auth.register_user(db=db, username=user.username, password=user.password, role=user.role)
    access_token = auth.create_jwt_token(data={"sub": new_user.username, "role": new_user.role})
    return {"access_token": access_token, "token_type": "bearer"}

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
