import datetime
import json
import logging
import random

from sqlalchemy.exc import IntegrityError

import tasks
import sqlalchemy as sa

from sqlalchemy.orm import Session

from flask import Blueprint, jsonify, request, make_response

from datamodel import (
    ExecutionType,
    TaskModel,
    TaskStatus,
    engine,
    TaskResultModel,
    ResultStatus, DeviceModel,
)

devices_blueprint = Blueprint("devices", __name__)

logger = logging.getLogger()


def get_device_tasks(device_id):
    """Busca las tareas que tiene que ejecutar cierto dispositivo."""

    serialized_results = []

    with Session(engine) as session:
        query = (
            sa.select(TaskResultModel)
            .join(TaskResultModel.task)
            .where(
                TaskResultModel.device_id == device_id,
                TaskResultModel.status == ResultStatus.pending,
            )
        )
        results = session.execute(query)
        results = results.scalars().all()
        serialized_results = [tasks.serialize_task(res) for res in results]

    return serialized_results


def parse_results(results):
    new_results = {}
    for res in results:
        if "not_supported" in res:
            new_results[res["id"]] = "not_supported"
        else:
            new_results[res["id"]] = res["value"]
    return new_results



def store_task_results(device_id, results):
    """Guarda los resultados de las tareas"""

    logger.info(f"Storing {results}")

    map_results = parse_results(results)

    with Session(engine) as session:
        query = (
            sa.select(TaskResultModel)
            .join(TaskResultModel.task)
            .where(
                TaskResultModel.device_id == device_id,
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
                # Si la respuesta del dispositivo fue "not supported" entonces le ponemos ese estado
                # al resultado y terminamos, no se crea un nuevo resultado pendiente si era periodica.
                q_res.status = ResultStatus.not_supported
            else:
                q_res.status = ResultStatus.done
                q_res.value = value
                # Generamos un nuevo resultado pendiente si la tarea asociada es periodica y está activa.
                if (
                    q_res.task.execution_type == ExecutionType.periodic
                    and q_res.task.status == TaskStatus.active
                ):
                    logger.info(
                        f"Creando nuevo resultado con estado pendiente para la tarea {q_res.task.id} (periodica)"
                    )
                    next_results.append(
                        TaskResultModel(task_id=q_res.task.id, device_id=device_id)
                    )

        session.add_all(next_results)
        session.commit()


@devices_blueprint.route("/tasks/<device_id>", methods=["GET", "POST"])
def tasks_endpoint(device_id):
    if request.method == "POST":
        logger.info(f"Adding new entry for device id: {device_id}")

        # Aca asumimos que nos llega algo como
        # [{ 'id': <result_id>, 'value': <valor medido> }, ...]
        tasks_results = json.loads(request.data)

        # Es un resultado de alguna tarea
        store_task_results(device_id, tasks_results)

        return make_response(jsonify("ok"), 200)
    else:
        _tasks = get_device_tasks(device_id)

        return make_response(jsonify(tasks=list(_tasks)), 200)


@devices_blueprint.route("/<device_id>", methods=["POST", "DELETE"])
def devices_endpoint(device_id):
    if request.method == "POST":
        try:
            device = DeviceModel(name=device_id)
            with Session(engine) as session:
                session.add_all([device])
                session.commit()
                return "ok", 200
        except IntegrityError:
            return "Device already exists", 400
    if request.method == 'DELETE':
        with Session(engine) as session:
            session.query(DeviceModel).filter(DeviceModel.name == device_id).delete()
            session.commit()
        return make_response("Deleted OK", 200)


@devices_blueprint.route("/", methods=["GET"])
def devices_get_all_endpoint():
    if request.method == 'GET':
        with Session(engine) as session:
            devices = session.query(DeviceModel)
            return {
                'devices': list({"id": x.name} for x in devices)
            }, 200
