import uuid
import datetime

LED_ON_TASK     =  {'name': 'led_on', 'config': {}}
LED_OFF_TASK    =  {'name': 'led_off', 'config': {}}
READ_INPUT      =  {'name': 'read', 'config': {}}

class Task(object):

    def __init__(self, name):
        self.uuid = uuid.uuid1()
        self.created_at = datetime.datetime.now()
        self.name = name

    def is_periodic(self):
        return False


class PeriodicTask(Task):

    def __init__(self, name):
        super().__init__(name)

    def is_periodic(self):
        return True


def build_task(task_name):
    return Task(task_name)

def serialize_task(task):
    return { 
        'id': task.id,
        'task_name': task.task.name,
        'task_params': task.task.task_params
    }
