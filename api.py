from flask import Blueprint, make_response, jsonify

from db import db, pending_tasks, KNOWN_DEVICES_ID
from tasks import build_task

api_blueprint = Blueprint('api', __name__)

def add_taks_to_device(device_id, task):
    device_pending = pending_tasks.get(device_id)

    if device_pending is None: return

    device_pending.add(task)
    pending_tasks[device_id] = device_pending


def build_measurements():
    # Aca podriamos recibir filtros para obtener mediciones
    # pero por lo pronto devolvemos todos los resultados para
    # cada uno de los dispositivos.

    return db


@api_blueprint.route('/measurements', methods=['GET'])
def get_measures():
    measurements = build_measurements()
    return make_response(jsonify(measurements), 200)

@api_blueprint.route('/queue-once', methods=['POST'])
def queue_once():
    # Si no recibimos un device_id la
    # encolamos a todos los dispositivos.

    task = build_task('led_on')

    for device_id in KNOWN_DEVICES_ID:
        add_taks_to_device(device_id, task)

    return make_response('ok', 200)

@api_blueprint.route('/schedule-task', methods=['POST'])
def schedule_task():
    # Tareas periodicas.

    return make_response('ok', 200)

@api_blueprint.route('/remove-task', methods=['POST'])
def remove_task():
    # TODO
    return make_response('ok', 200)
