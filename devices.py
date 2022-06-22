import json
import logging
import random
import tasks
import sqlalchemy as sa

from sqlalchemy.orm import Session

from flask import Blueprint, jsonify, request, make_response

from datamodel import engine, TaskResultModel, ResultStatus

devices_blueprint = Blueprint('devices', __name__)

logger = logging.getLogger()

def get_device_tasks(device_id):

    # Busca las tareas que tiene que ejecutar cierto dispositivo.

    results = []

    with Session(engine) as session:
        query = sa.select(TaskResultModel).where(
            TaskResultModel.device_id == device_id,
            TaskResultModel.status == ResultStatus.pending
        )
        results = session.execute(query)
        results = results.scalars().all()

    # tasks = [
    #     tasks.READ_INPUT,
    #     tasks.LED_ON_TASK if random.getrandbits(1) else tasks.LED_OFF_TASK
    # ]

    return results

def store_task_results(device_id, results):
    # Guarda los resultados de las tareas

    logger.info(f'Storing {results}')

    for result in results:
        result_id, result_value = result['id'], result['value']

        # Actualizamos los resultados.

        with Session(engine) as session:
            session \
                .query(TaskResultModel) \
                .filter(
                    TaskResultModel.device_id == device_id,
                    TaskResultModel.status == ResultStatus.pending,
                    TaskResultModel.id == result_id
                ) \
                .update({ 'value': result_value, 'status': ResultStatus.done })

            session.commit()


@devices_blueprint.route('/tasks/<device_id>', methods=['GET', 'POST'])
def tasks_endpoint(device_id):
    if request.method == 'POST':
        logger.info(f'Adding new entry for device id: {device_id}')

        # Aca asumimos que nos llega algo como
        # [{ 'id': <result_id>, 'value': <valor medido> }, ...]

        tasks_results = json.loads(request.data)

        # Es un resultado de alguna tarea
        store_task_results(device_id, tasks_results)

        return make_response(jsonify('ok'), 200)
    else:
        # La sacamos de las pendientes, o generamos una nueva
        # si es periodica.

        _tasks = map(lambda task: tasks.serialize_task(task), get_device_tasks(device_id))

        return make_response(jsonify(tasks=list(_tasks)), 200)
