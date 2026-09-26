from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database file location in backend directory
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "agri_advisory.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models to ensure they are registered with Base
    import models.user  # noqa: F401
    import models.analysis  # noqa: F401
    Base.metadata.create_all(bind=engine)
