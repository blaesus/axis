from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL

from axis_scrape import settings

DeclarativeBase = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    return create_engine(URL(**settings.DATABASE))


def create_deals_table(engine):
    """"""
    DeclarativeBase.metadata.create_all(engine)


class Reports(DeclarativeBase):
    """Sqlalchemy reports model"""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=True)
    html = Column(String, nullable=True)
    title = Column(String, nullable=True)
    order = Column(Integer)
    type = Column(String, nullable=True)
    pub_date = Column(DateTime)
    scrape_time_utc = Column(DateTime)
    main_text = Column(String, nullable=True)
