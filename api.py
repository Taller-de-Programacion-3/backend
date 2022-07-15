import logging
import json
from sqlalchemy import null

from sqlalchemy.orm import Session
from flask import Blueprint, make_response, jsonify, request
from tasks import build_task

from datamodel import ExecutionType, engine, TaskModel, TaskResultModel

KNOWN_DEVICES_ID = ['esp32', 'riscv', 'argon', 'test']

logger = logging.getLogger()

def build_measurements():
    # Aca podriamos recibir filtros para obtener mediciones
    # pero por lo pronto devolvemos todos los resultados para
    # cada uno de los dispositivos.

    # TODO
    return {}


def handle_create_task(body):
    # Lista de dispositivos en los que se carga la tarea.
    devices_ids = body.get('device_ids')

    for id in devices_ids:
        if id not in KNOWN_DEVICES_ID:
            raise RuntimeError("Invalid device id")

    if not body.get("task_name") or not body.get("device_ids"):
        raise RuntimeError("Invalid empty params")

    logger.info(f'Creando tarea {body.get("task_name")} para {devices_ids}')

    execution_type = ExecutionType.periodic if body.get('periodic') else ExecutionType.once

    task_params = {}
    if body.get('task_params') is not None:
        task_params = body.get('task_params')

    sense_config = body.get('sense_config') if body.get('sense_config') else {}
    
    task = TaskModel(
        name=body.get('task_name'),
        execution_type=execution_type,
        task_params=task_params
    )

    with Session(engine) as session:
        session.add(task)

        # TODO. validar ids
        task_results = [
            TaskResultModel(task_id=task.id, device_id=device_id) for device_id in devices_ids
        ]

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
    try:
        body = json.loads(request.data)
        if request.method == 'POST':
            return handle_create_task(body)

        elif request.method == 'DELETE':
            return handle_remove_task(body)

        elif request.method == 'PATCH':
            return handle_modify_task(body)

    except RuntimeError:
        return make_response("Invalid params", 400)

