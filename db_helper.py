from datamodel import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

def db_operator(exec_operation):
    def wrapper(*args, **kwargs):
        session_maker = sessionmaker(bind=create_engine(os.environ.get('DB_URL')))
        with session_maker() as session_instance:
            try:
                exec_operation(*args, session=session_instance)
                session_instance.commit()
            finally:
                session_instance.close()

    return wrapper

class Persistable:
    @db_operator
    def insert(self, session=None):
        session.add(self.record)

    @db_operator
    def delete(self, session=None):
        session.delete(self.record)

class Task(Persistable):
    def __init__(self, device_id, name, exec_type='QUEUEABLE'):
        self.record = TaskModel(device_id=device_id, name=name, execution_type=exec_type)


