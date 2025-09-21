from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------- Database setup --------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///app.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# -------------------- Models --------------------

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), nullable=False)  # "candidate" or "company"
    created_at = Column(DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(256), nullable=False)
    content_text = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, nullable=False)
    job_id = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    matched_skills = Column(Text, nullable=True)
    missing_skills = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# -------------------- Create tables --------------------
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created successfully ✅")
