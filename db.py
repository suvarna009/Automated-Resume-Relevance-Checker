# db.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "app.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="")
    email = Column(String, default="")
    role = Column(String, default="candidate")  # candidate | company | admin
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company_name = Column(String, default="")
    location = Column(String, default="")
    jd_text = Column(Text, default="")
    must_skills = Column(Text, default="")   # comma separated
    nice_skills = Column(Text, default="")   # comma separated
    created_at = Column(DateTime, default=datetime.utcnow)


class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String)
    filepath = Column(String)
    parsed_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", backref="resumes")


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    hard_score = Column(Float)  # percent 0-100
    soft_score = Column(Float)  # percent 0-100
    total_score = Column(Float)  # percent 0-100
    verdict = Column(String)     # High/Medium/Low
    missing_must = Column(Text)  # csv
    missing_nice = Column(Text)  # csv
    feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    if not os.path.exists(DB_PATH):
        Base.metadata.create_all(bind=engine)

# Initialize DB on import (safe)
init_db()
