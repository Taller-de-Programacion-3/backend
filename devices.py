import json
import logging
import random
import tasks
import sqlalchemy as sa

from sqlalchemy.orm import Session

from flask import Blueprint, jsonify, request, make_response

from datamodel import ExecutionType, TaskModel, engine, TaskResultModel, ResultStatus

devices_blueprint = Blueprint('devices', __name__)

logger = logging.getLogger()

def get_device_tasks(device_id):

    # Busca las tareas que tiene que ejecutar cierto dispositivo.


    serialized_results = []
    with Session(engine) as session:
        query = sa.select(TaskResultModel).join(TaskResultModel.task).where(
            TaskResultModel.device_id == device_id,
            TaskResultModel.status == ResultStatus.pending
        )
        results = session.execute(query)
        results = results.scalars().all()
        serialized_results = [tasks.serialize_task(res) for res in results]
    # tasks = [
    #     tasks.READ_INPUT,
    #     tasks.LED_ON_TASK if random.getrandbits(1) else tasks.LED_OFF_TASK
    # ]

    return serialized_results

def store_task_results(device_id, results):
    # Guarda los resultados de las tareas

    logger.info(f'Storing {results}')

    map_results = {res['id'] : res['value'] for res in results}

    query_result = [] 
    with Session(engine) as session:
        query = sa.select(TaskResultModel).join(TaskResultModel.task).where(
            TaskResultModel.device_id == device_id,
            TaskResultModel.status == ResultStatus.pending,
            TaskResultModel.id.in_(map_results.keys())
        )
        query_result = session.execute(query)
        query_result = query_result.scalars().all()

        next_results = []
        # Actualizamos los resultados.
        for q_res in query_result:
            q_res.status = ResultStatus.done
            q_res.value = map_results.get(q_res.id)
   
            # Generamos un nuevo resultado pendiente si la tarea asociada es periodica.
            if q_res.task.execution_type == ExecutionType.periodic:
                logger.info(f'Creating new pending result for periodic task {q_res.task.id}')
                next_results.append(TaskResultModel(task_id=q_res.task.id, device_id=device_id))

        session.add_all(next_results)
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

        _tasks = get_device_tasks(device_id)

        return make_response(jsonify(tasks=list(_tasks)), 200)
