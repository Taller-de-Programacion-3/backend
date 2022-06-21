import json
import logging
import random
import tasks
import sqlalchemy as sa

from datamodel import TaskResultModel, ResultStatus

from flask import Blueprint, jsonify, request, make_response
from db import db, pending_tasks

devices_blueprint = Blueprint('devices', __name__)

logger = logging.getLogger()

def get_device_tasks(device_id):

    # Busca las tareas que tiene que ejecutar cierto dispositivo.

    device_tasks = pending_tasks.get(device_id)

    # tasks = [
    #     tasks.READ_INPUT,
    #     tasks.LED_ON_TASK if random.getrandbits(1) else tasks.LED_OFF_TASK
    # ]

    return device_tasks


def update_pending_tasks(device_id):
    updated_tasks = set()

    for task in pending_tasks.get(device_id, set()):
        if task.is_periodic():
            # TODO
            pass

    pending_tasks[device_id] = updated_tasks

def store_task_results(device_id, results):
    # Guarda los resultados de las tareas

    logger.info(f'Storing {results}')

    for result in results:
        task_id, task_result = result['id'], result['value']

        device_results = db.get(device_id, {})
        device_results[task_id] = task_result
        db[device_id] = device_results


@devices_blueprint.route('/tasks/<device_id>', methods=['GET', 'POST'])
def tasks_endpoint(device_id):
    if request.method == 'POST':
        logger.info(f'Adding new entry for device id: {device_id}')

        tasks_results = json.loads(request.data)

        # Es un resultado de alguna tarea
        store_task_results(device_id, tasks_results)

        return make_response(jsonify('ok'), 200)
    else:
        # La sacamos de las pendientes, o generamos una nueva
        # si es periodica.

        _tasks = map(lambda task: tasks.serialize_task(task), get_device_tasks(device_id))

        # Limpiamos las no periodicas y generamos
        # nuevas instancias para las periodicas.
        update_pending_tasks(device_id)

        return make_response(jsonify(tasks=list(_tasks)), 200)
