import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'child', 'parent', 'admin'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    trips = relationship("Trip", back_populates="user")
    geofences = relationship("Geofence", back_populates="user")
    alerts = relationship("Alert", back_populates="user")

    # For parent-child relationships
    children = relationship("ParentChild", foreign_keys="[ParentChild.parent_id]", back_populates="parent")
    parents = relationship("ParentChild", foreign_keys="[ParentChild.child_id]", back_populates="child")

class ParentChild(Base):
    __tablename__ = 'parent_child'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('users.id'))
    child_id = Column(Integer, ForeignKey('users.id'))

    parent = relationship("User", foreign_keys=[parent_id], back_populates="children")
    child = relationship("User", foreign_keys=[child_id], back_populates="parents")

class Geofence(Base):
    __tablename__ = 'geofences'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_m = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="geofences")

class Trip(Base):
    __tablename__ = 'trips'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    session_hash = Column(String, unique=True, nullable=False)
    mode = Column(String) # 'college', 'flight', 'train', 'road'
    status = Column(String, default='active') # 'active', 'ended', 'paused'
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)

    user = relationship("User", back_populates="trips")
    details = relationship("TripDetail", back_populates="trip")
    locations = relationship("Location", back_populates="trip")

class TripDetail(Base):
    __tablename__ = 'trip_details'
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id'))
    detail_type = Column(String) # e.g., 'flight_number', 'origin', 'destination'
    value = Column(Text)

    trip = relationship("Trip", back_populates="details")

class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.id'))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    battery = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    trip = relationship("Trip", back_populates="locations")

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    trip_id = Column(Integer, ForeignKey('trips.id'), nullable=True)
    alert_type = Column(String) # e.g., 'geofence_enter', 'low_battery'
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="alerts")
