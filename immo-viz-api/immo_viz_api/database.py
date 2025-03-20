import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

VIZ_DATABASE_URL = os.environ["VIZ_DATABASE_URL"]
MONITORING_DATABASE_URL = os.environ["MONITORING_DATABASE_URL"]

viz_engine = create_engine(VIZ_DATABASE_URL)
monitoring_engine = create_engine(MONITORING_DATABASE_URL)

VizDatabaseSession = sessionmaker(autocommit=False, autoflush=False, bind=viz_engine)
MonitoringDatabaseSession = sessionmaker(autocommit=False, autoflush=False, bind=monitoring_engine)

VizBase = declarative_base()
MonitoringBase = declarative_base()


def get_viz_db():
    db = VizDatabaseSession()
    try:
        yield db
    finally:
        db.close()


def get_monitoring_db():
    db = MonitoringDatabaseSession()
    try:
        yield db
    finally:
        db.close()
