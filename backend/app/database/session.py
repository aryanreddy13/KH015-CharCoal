import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def mask_db_url(url: str) -> str:
    if "@" in url and "://" in url:
        scheme_user = url.split("@")[0]
        host_part = url.split("@")[1]
        if ":" in scheme_user:
            prefix = scheme_user.rsplit(":", 1)[0]
            return f"{prefix}:*****@{host_part}"
    return url

def get_engine():
    db_url = settings.DATABASE_URL.strip() if settings.DATABASE_URL else "sqlite:///./disaster.db"
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    try:
        if db_url.startswith("sqlite"):
            engine = create_engine(db_url, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_recycle=300,
                connect_args={"connect_timeout": 5},
            )
            # verify connection
            with engine.connect() as conn:
                pass
            logger.info(f"Connected to PostgreSQL database at {mask_db_url(db_url)}")
        return engine
    except Exception as e:
        logger.warning(f"Database connection to '{mask_db_url(db_url)}' failed: {e}. Falling back to SQLite local database.")
        sqlite_fallback = "sqlite:///./disaster.db"
        return create_engine(sqlite_fallback, connect_args={"check_same_thread": False})

def upgrade_schema(eng):
    """
    Safely ensures newly added model columns and tables exist in PostgreSQL/SQLite without dropping existing data.
    """
    from sqlalchemy import text
    from app.models.models import Base
    
    # Create all new tables (e.g. resource_allocations)
    try:
        Base.metadata.create_all(bind=eng)
    except Exception as e:
        logger.debug(f"Base.metadata.create_all: {e}")

    dialect = eng.dialect.name
    try:
        with eng.begin() as conn:
            if dialect == "postgresql":
                try:
                    conn.execute(text("SET lock_timeout = '2s';"))
                except Exception:
                    pass
                try:
                    conn.execute(text("ALTER TABLE agencies ADD COLUMN IF NOT EXISTS email VARCHAR(255);"))
                except Exception:
                    pass
            else:
                try:
                    conn.execute(text("ALTER TABLE agencies ADD COLUMN email VARCHAR(255);"))
                except Exception:
                    pass

            # 2. Resources columns
            res_cols = [
                ("total_quantity", "INTEGER DEFAULT 1"),
                ("available_quantity", "INTEGER DEFAULT 1"),
                ("reserved_quantity", "INTEGER DEFAULT 0"),
                ("allocated_quantity", "INTEGER DEFAULT 0"),
                ("unit", "VARCHAR(50) DEFAULT 'Units'"),
                ("location", "VARCHAR(255)"),
            ]
            for col_name, col_type in res_cols:
                try:
                    if dialect == "postgresql":
                        conn.execute(text(f"ALTER TABLE resources ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                    else:
                        conn.execute(text(f"ALTER TABLE resources ADD COLUMN {col_name} {col_type};"))
                except Exception:
                    pass

            # 3. SOSEvent columns
            cols = [
                ("provider_status", "VARCHAR(50) DEFAULT 'NEW'"),
                ("disaster_type", "VARCHAR(100) DEFAULT 'Flood'"),
                ("severity", "FLOAT DEFAULT 9.5"),
                ("people_affected", "INTEGER DEFAULT 1"),
                ("injured_people", "INTEGER DEFAULT 0"),
                ("missing_people", "INTEGER DEFAULT 0"),
                ("food_required", "BOOLEAN DEFAULT FALSE"),
                ("food_quantity", "INTEGER"),
                ("water_required", "BOOLEAN DEFAULT FALSE"),
                ("water_quantity", "INTEGER"),
                ("shelter_required", "BOOLEAN DEFAULT FALSE"),
                ("shelter_quantity", "INTEGER"),
                ("medicine_required", "BOOLEAN DEFAULT FALSE"),
                ("medicine_quantity", "INTEGER"),
                ("rescue_required", "BOOLEAN DEFAULT FALSE"),
                ("rescue_units_required", "INTEGER"),
                ("ambulance_required", "BOOLEAN DEFAULT FALSE"),
                ("ambulances_required", "INTEGER"),
                ("required_resources_json", "TEXT"),
                ("notified_agencies_json", "TEXT"),
                ("photo_url", "VARCHAR(500)"),
                ("distance_km", "FLOAT DEFAULT 4.8"),
                ("eta_minutes", "INTEGER DEFAULT 11"),
                ("assigned_agency_id", "VARCHAR(36)"),
                ("assigned_resource_id", "VARCHAR(36)"),
                ("resend_status", "VARCHAR(50) DEFAULT 'NOT_SENT'"),
                ("pagerduty_status", "VARCHAR(50) DEFAULT 'NOT_SENT'"),
                ("assessment_json", "JSONB" if dialect == "postgresql" else "JSON"),
                ("assessment_version", "VARCHAR(50)"),
                ("assessment_status", "VARCHAR(50)"),
                ("priority_assessment_json", "JSONB" if dialect == "postgresql" else "JSON"),
                ("priority_score", "FLOAT"),
                ("priority_level", "VARCHAR(50)"),
                ("priority_scoring_version", "VARCHAR(50)"),
                ("updated_at", "TIMESTAMP"),
            ]
            for col_name, col_type in cols:
                try:
                    if dialect == "postgresql":
                        conn.execute(text(f"ALTER TABLE sos_events ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                    else:
                        conn.execute(text(f"ALTER TABLE sos_events ADD COLUMN {col_name} {col_type};"))
                except Exception:
                    pass

            # 4. Reports columns
            report_cols = [
                ("assessment_json", "JSONB" if dialect == "postgresql" else "JSON"),
                ("assessment_version", "VARCHAR(50)"),
                ("assessment_status", "VARCHAR(50)"),
                ("priority_assessment_json", "JSONB" if dialect == "postgresql" else "JSON"),
                ("priority_score", "FLOAT"),
                ("priority_level", "VARCHAR(50)"),
                ("priority_scoring_version", "VARCHAR(50)"),
            ]
            for col_name, col_type in report_cols:
                try:
                    if dialect == "postgresql":
                        conn.execute(text(f"ALTER TABLE reports ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                    else:
                        conn.execute(text(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type};"))
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Schema upgrade notice: {e}")

engine = get_engine()
try:
    upgrade_schema(engine)
except Exception as e:
    logger.warning(f"Schema upgrade notice: {e}")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
