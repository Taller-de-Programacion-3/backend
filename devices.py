import json
import logging
import random

from flask import Blueprint, jsonify, request, make_response
from db import db

LED_ON_TASK     =  {'name': 'led_on', 'config': {}}
LED_OFF_TASK    =  {'name': 'led_off', 'config': {}}
READ_INPUT      =  {'name': 'read', 'config': {}}

devices_blueprint = Blueprint('devices', __name__)

def get_device_tasks(device_id):
    # Busca las tareas que tiene que ejecutar cierto dispositivo.

    tasks = [
        READ_INPUT,
        LED_ON_TASK if random.getrandbits(1) else LED_OFF_TASK
    ]

    return task

def store_task_results(device_id, results):
    # Guarda los resultados de las tareas

    for result in tasks_results:
        task_name, task_result = result['name'], result['value']

        device_results = db.get(device_id, {})
        device_results[task_name] = task_result

        db[device_id] = device_results


@devices_blueprint.route('/tasks/<device_id>', methods=['GET', 'POST'])
def get_tasks(device_id):
    if request.method == 'POST':

        logger.info(f'Adding new entry for device id: {device_id}')

        # Es un resultado de alguna tarea
        store_task_results(device_id, json.loads(request.data))
        return make_response(jsonify([]), 200)

    else:
        tasks = get_device_tasks(device_id)
        return make_response(jsonify(tasks=tasks), 200)
