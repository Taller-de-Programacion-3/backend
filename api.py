import json
import logging
from json import JSONDecodeError

from flask import Blueprint, make_response, jsonify, request
from sqlalchemy.orm import Session

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
            return "Invalid device id", 400

    if len(devices_ids) < 1:
        return 'Must add at least one device Id', 400

    if not body.get("task_name") or not body.get("device_ids"):
        return "Invalid empty params", 400

    logger.info(f'Creando tarea {body.get("task_name")} para {devices_ids}')

    execution_type = ExecutionType.periodic if body.get('periodic') else ExecutionType.once

    task_params = {}
    if body.get('task_params') is not None:
        task_params = body.get('task_params')

    task = TaskModel(
        name=body.get('task_name'),
        execution_type=execution_type,
        task_params=task_params
    )

    with Session(engine) as session:
        session.add(task)

        
        session.commit()    # Need to commit to link by task.id
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


def row2dict(row: TaskModel):
    d = {}
    for column in row.__table__.columns:
        val = row.__getattribute__(column.name)
        try:
            d[column.name] = json.loads(val)
        except (TypeError, JSONDecodeError):
            d[column.name] = val
    return d


def handle_get_active_tasks():
    with Session(engine) as session:
        results = []
        for row in session.query(TaskModel).filter(TaskModel.status == 'active'):
            results.append(row2dict(row))
        return make_response(jsonify(results))


api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/measurements', methods=['GET'])
def get_measures():
    measurements = build_measurements()
    return make_response(jsonify(measurements), 200)


@api_blueprint.route('/task', methods=['POST', 'DELETE', 'PATCH', 'GET'])
def task():
    try:
        body = json.loads(request.data) if request.data else {}

        if request.method == 'POST':
            return handle_create_task(body)

        if request.method == 'DELETE':
            return handle_remove_task(body)

        if request.method == 'PATCH':
            return handle_modify_task(body)

        if request.method == 'GET':
            return handle_get_active_tasks()

    except RuntimeError:
        return make_response("Invalid params", 400)


