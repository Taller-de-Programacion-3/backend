from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TaskModel(Base):
    __tablename__ = 'tasks'

    device_id = Column(String, nullable=False, primary_key=True)
    name = Column(String, nullable=False, primary_key=True)
    execution_type = Column(String, default='QUEUEABLE')
    created = Column(DateTime, default=datetime.utcnow)

