import os
import enum
import sqlalchemy as sa

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

db_url = os.environ.get('DB_URL')
engine = create_engine(db_url)

Base = declarative_base()

class ResultStatus(enum.Enum):
    pending = 'pending'
    done = 'done'

class ExecutionType(enum.Enum):
    once = 'once'
    periodic = 'periodic'

class TaskStatus(enum.Enum):
    active = 'active'
    inactive = 'inactive'


# Representa una tarea + configuracion para realizarse

class TaskModel(Base):

    __tablename__ = 'tasks'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    name = sa.Column(sa.String, nullable=False)

    created_at = sa.Column(
        sa.DateTime, nullable=False, server_default=sa.text('NOW()')
    )

    execution_type = sa.Column(
        sa.Enum(ExecutionType),
        server_default='once',
        nullable=False
    )

    status = sa.Column(sa.Enum(TaskStatus), server_default='active')
    results = sa.orm.relationship('TaskResultModel')


# Representa el resultado de una tarea. Si el dispositivo
# no respondio se encontrara en estado pending.

class TaskResultModel(Base):

    __tablename__ = 'task_results'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    task_id = sa.Column(sa.Integer, sa.ForeignKey('tasks.id'))
    value = sa.Column(sa.String)
    device_id = sa.Column(sa.String, nullable=False)

    status = sa.Column(sa.Enum(ResultStatus), server_default='pending')
