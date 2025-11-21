"""
SQLAlchemy ORM Models for Project Sanjaya v2.1
Database: SQLite (portable to PostgreSQL)
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class RoleEnum(enum.Enum):
    """User roles"""
    child = "child"
    parent = "parent"
    admin = "admin"


class TripModeEnum(enum.Enum):
    """Trip tracking modes"""
    college = "college"
    flight = "flight"
    train = "train"
    road = "road"


class TripStatusEnum(enum.Enum):
    """Trip status"""
    active = "active"
    paused = "paused"
    ended = "ended"


class AlertTypeEnum(enum.Enum):
    """Alert types"""
    departure = "departure"
    arrival = "arrival"
    geofence_entry = "geofence_entry"
    geofence_exit = "geofence_exit"
    landing = "landing"
    home_arrival = "home_arrival"


class User(Base):
    """User model - supports child, parent, and admin roles"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    geofences = relationship("Geofence", back_populates="user", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    
    # Parent-child relationships
    children = relationship(
        "ParentChild",
        foreign_keys="ParentChild.parent_id",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    parents = relationship(
        "ParentChild",
        foreign_keys="ParentChild.child_id",
        back_populates="child",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role.value})>"


class ParentChild(Base):
    """Parent-child linking table"""
    __tablename__ = "parent_child"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("User", foreign_keys=[parent_id], back_populates="children")
    child = relationship("User", foreign_keys=[child_id], back_populates="parents")
    
    def __repr__(self):
        return f"<ParentChild(parent_id={self.parent_id}, child_id={self.child_id})>"


class Geofence(Base):
    """Geofence definitions - Home, College, Custom places"""
    __tablename__ = "geofences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # Home, College, Mall, etc.
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    radius_m = Column(Float, nullable=False)  # Radius in meters
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="geofences")
    
    def __repr__(self):
        return f"<Geofence(id={self.id}, name={self.name}, user_id={self.user_id})>"


class Trip(Base):
    """Trip tracking - college or travel mode"""
    __tablename__ = "trips"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mode = Column(Enum(TripModeEnum), nullable=False)
    status = Column(Enum(TripStatusEnum), default=TripStatusEnum.active, nullable=False)
    session_hash = Column(String(64), unique=True, nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="trips")
    details = relationship("TripDetail", back_populates="trip", uselist=False, cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="trip", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Trip(id={self.id}, user_id={self.user_id}, mode={self.mode.value}, status={self.status.value})>"


class TripDetail(Base):
    """Trip-specific details - flight number, train, route, etc."""
    __tablename__ = "trip_details"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, unique=True)
    details_json = Column(Text, nullable=True)  # JSON string with flight_number, train_number, etc.
    start_place = Column(String(200), nullable=True)
    end_place = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trip = relationship("Trip", back_populates="details")
    
    def __repr__(self):
        return f"<TripDetail(id={self.id}, trip_id={self.trip_id})>"


class Location(Base):
    """Location updates during a trip"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    battery = Column(Integer, nullable=True)  # Battery percentage
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    trip = relationship("Trip", back_populates="locations")
    
    def __repr__(self):
        return f"<Location(id={self.id}, trip_id={self.trip_id}, lat={self.lat}, lon={self.lon})>"


class Alert(Base):
    """Alerts for parents - departure, arrival, geofence events"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    alert_type = Column(Enum(AlertTypeEnum), nullable=False)
    read = Column(Integer, default=0)  # 0 = unread, 1 = read
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, user_id={self.user_id}, type={self.alert_type.value})>"