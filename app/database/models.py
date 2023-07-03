from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, ForeignKey, Integer, String, Float

SQLALCHEMY_DATABASE_URL = "sqlite:///./app/database/eq_monitor.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Model DB
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    files = relationship("FileDB", back_populates="user")


class FileDB(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    path = Column(String, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    upload_date = Column(String, nullable=False)
    type = Column(String, nullable=False)
    epc_date = Column(String, nullable=False)
    epc_lat = Column(Float, nullable=False)
    epc_lon = Column(Float, nullable=False)
    user = relationship("UserDB", back_populates="files")


Base.metadata.create_all(bind=engine)