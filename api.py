import logging

from sqlalchemy.orm import Session
from flask import Blueprint, make_response, jsonify, request
from tasks import build_task

from datamodel import engine, TaskModel, TaskResultModel

KNOWN_DEVICES_ID = ['esp32', 'riscv', 'argon','test']

logger = logging.getLogger()

def build_measurements():
    # Aca podriamos recibir filtros para obtener mediciones
    # pero por lo pronto devolvemos todos los resultados para
    # cada uno de los dispositivos.

    # TODO
    return {}


def handle_create_task(request):
    logger.info(f'Creando tarea "led_on"...')

    with Session(engine) as session:
        task = TaskModel(name='led_on')
        session.add(task)
        session.commit()

        task_results = [TaskResultModel(task_id=task.id, device_id=device_id) for device_id in KNOWN_DEVICES_ID]
        session.add_all(task_results)
        session.commit()

    return make_response('Created OK', 201)


def handle_remove_task(request):
    return make_response('Deleted OK', 201)


api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/measurements', methods=['GET'])
def get_measures():
    measurements = build_measurements()
    return make_response(jsonify(measurements), 200)


@api_blueprint.route('/task', methods=['POST','DELETE'])
def task():
    if request.method == 'POST':
        return handle_create_task(request)

    elif request.method == 'DELETE':
        return handle_remove_task(request)

