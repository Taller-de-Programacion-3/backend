import datetime
import json
import logging
import random

import tasks
import sqlalchemy as sa

from sqlalchemy.orm import Session

from flask import Blueprint, jsonify, request, make_response

from datamodel import (
    ExecutionType,
    TaskStatus,
    engine,
    TaskResultModel,
    ResultStatus,
    DeviceModel,
    DeviceStatus,
    TaskModel
)

devices_blueprint = Blueprint("devices", __name__)

logger = logging.getLogger()


def get_device_tasks(device_key):
    """Busca las tareas que tiene que ejecutar cierto dispositivo."""

    serialized_results = []

    with Session(engine) as session:
        query = (
            sa.select(TaskResultModel)
            .join(DeviceModel)
            .join(TaskModel)
            .where(
                DeviceModel.key == device_key,
                TaskResultModel.status == ResultStatus.pending,
                TaskModel.status == TaskStatus.active
            )
        )
        results = session.execute(query)
        results = results.scalars().all()
        serialized_results = [tasks.serialize_task(res) for res in results]

    return serialized_results


def parse_results(results):
    new_results = {}

    for res in results:
        new_results[res["id"]] = "not_supported" if "not_supported" in res else res["value"]
    return new_results


def store_task_results(key, results):
    """Guarda los resultados de las tareas"""

    logger.info(f"Storing {results}")

    map_results = parse_results(results)

    with Session(engine) as session:

        target_device = [x for x in session.query(DeviceModel).filter(DeviceModel.key == key)]

        # Buscamos que exista el dispositivo.
        target_device = target_device[0]

        query = (
            sa.select(TaskResultModel)
            .join(TaskResultModel.task)
            .where(
                TaskResultModel.device_id == target_device.id,
                TaskResultModel.status == ResultStatus.pending,
                TaskResultModel.id.in_(map_results.keys()),
            )
        )
        query_result = session.execute(query).scalars().all()

        next_results = []

        # Actualizamos los resultados.
        for q_res in query_result:
            value = map_results.get(q_res.id)
            q_res.completed_at = datetime.datetime.now()

            if value == "not_supported":

                # Si la respuesta del dispositivo fue "not supported" entonces le ponemos ese
                # estado al resultado y terminamos, no se crea un nuevo resultado pendiente si
                # era periodica.
                q_res.status = ResultStatus.not_supported
            else:
                q_res.status = ResultStatus.done
                q_res.value = value

                # Generamos un nuevo resultado pendiente si la tarea asociada es
                # periodica, está activa y el dispositivo esta activo.
                if (
                    q_res.task.execution_type == ExecutionType.periodic
                    and q_res.task.status == TaskStatus.active
                    and target_device.status == DeviceStatus.active
                ):
                    logger.info(
                        f"Creando nuevo resultado con estado pendiente para la tarea {q_res.task.id} (periodica)"
                    )
                    next_results.append(
                        TaskResultModel(task_id=q_res.task.id, device_id=target_device.id)
                    )

        session.add_all(next_results)
        session.commit()


@devices_blueprint.route("/tasks/<device_key>", methods=["GET", "POST"])
def tasks_endpoint(device_key):
    if request.method == "POST":
        logger.info(f"Adding new entry for device id: {device_key}")

        # Aca asumimos que nos llega algo como
        # [{ 'id': <result_id>, 'value': <valor medido> }, ...]
        tasks_results = json.loads(request.data)

        # Es un resultado de alguna tarea
        store_task_results(device_key, tasks_results)

        return make_response(jsonify("ok"), 200)
    else:
        _tasks = get_device_tasks(device_key)

        return make_response(jsonify(tasks=list(_tasks)), 200)
