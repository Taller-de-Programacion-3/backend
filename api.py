import logging
import json
from sqlalchemy import null

from sqlalchemy.orm import Session
from flask import Blueprint, make_response, jsonify, request
from tasks import build_task

from datamodel import ExecutionType, engine, TaskModel, TaskResultModel

KNOWN_DEVICES_ID = ['esp32', 'riscv', 'argon','test']

logger = logging.getLogger()

def build_measurements():
    # Aca podriamos recibir filtros para obtener mediciones
    # pero por lo pronto devolvemos todos los resultados para
    # cada uno de los dispositivos.

    # TODO
    return {}


def handle_create_task(body):
    logger.info(f'Creando tarea "led_on"...')
    execution_type = ExecutionType.periodic if body.get('periodic') else ExecutionType.once
    sense_config = {}
    if body.get('sense_config') is not None:
        sense_config = body.get('sense_config')
    task = TaskModel(
        name = body.get('task_name'),
        execution_type = execution_type,
        sense_metric = sense_config.get('sense_metric'),
        sense_mode = sense_config.get('sense_mode'),
        sense_sample_rate = sense_config.get('sense_sample_rate'),
        sense_n_samples = sense_config.get('sense_n_samples')
    )
    with Session(engine) as session:
        session.add(task)
        session.commit()
        task_results = [TaskResultModel(task_id=task.id, device_id=device_id) for device_id in KNOWN_DEVICES_ID]
        session.add_all(task_results)
        session.commit()

    return make_response('Created OK', 201)


def handle_remove_task(body):
    with Session(engine) as session:
        session.query(TaskModel) \
            .filter(TaskModel.id == body.get('id')) \
            .delete()
        session.commit()
    return make_response('Deleted OK', 200)

def handle_modify_task(body):
    with Session(engine) as session:
        session.query(TaskModel) \
            .filter(TaskModel.id == body.get('id')) \
            .update({ 'status': body.get('status') })
        session.commit()
    return make_response('Modified OK', 200)

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/measurements', methods=['GET'])
def get_measures():
    measurements = build_measurements()
    return make_response(jsonify(measurements), 200)


@api_blueprint.route('/task', methods=['POST','DELETE','PATCH'])
def task():
    body = json.loads(request.data)
    if request.method == 'POST':
        return handle_create_task(body)

    elif request.method == 'DELETE':
        return handle_remove_task(body)

    elif request.method == 'PATCH':
        return handle_modify_task(body)

