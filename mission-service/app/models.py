from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class Generation(Base):
    __tablename__ = "generations"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    gen_number = Column(Integer)
    date_utc = Column(DateTime(timezone=True))
    complete = Column(Boolean, nullable=True)
    details = Column(Text, nullable=True)
    region_name = Column(String, nullable=True)
    games = Column(String, nullable=True)
    total_species = Column(Integer, nullable=True)
    pokemon_species = Column(JSONB, default=list)
    cached_at = Column(DateTime(timezone=True), server_default=func.now())


class Pokemon(Base):
    __tablename__ = "pokemon"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    height_m = Column(Float, nullable=True)
    mass_kg = Column(Float, nullable=True)
    types_count = Column(Integer, default=0)
    abilities_count = Column(Integer, default=0)
    abilities = Column(String, nullable=True)
    base_experience = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    sprite_url = Column(String, nullable=True)
    cached_at = Column(DateTime(timezone=True), server_default=func.now())
