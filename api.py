import json
import logging
import datetime

from json import JSONDecodeError

from flask import Blueprint, make_response, jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from datamodel import (
    ExecutionType,
    TaskStatus,
    engine,
    TaskModel,
    TaskResultModel,
    ResultStatus, DeviceModel,
)

KNOWN_DEVICES_ID = ["esp32", "riscv", "argon", "test"]

logger = logging.getLogger()


def parse_led_result(metrics, result, task):
    if "led" not in metrics[result.device_id]:
        metrics[result.device_id]["led"] = {}
    if "on" not in metrics[result.device_id]["led"]:
        metrics[result.device_id]["led"]["on"] = []
    metrics[result.device_id]["led"]["on"].append(
        {"value": 1 if task.name == "Led On" else 0, "timestamp": result.completed_at}
    )


def parse_sense_result(metrics, result, task):
    metric = task.task_params["sense_metric"]
    task_id = 'Task ID: {}'.format(task.id)
    if metric not in metrics[result.device_id]:
        metrics[result.device_id][metric] = {}
    if task_id not in metrics[result.device_id][metric]:
        metrics[result.device_id][metric][task_id] = []
    metrics[result.device_id][metric][task_id].append(
        {
            "value": result.value,
            "timestamp": result.completed_at,
        }
    )


def build_measurements(args):
    last_minutes = None
    if "last" in args:
        last_minutes = int(args.get("last"))

    with Session(bind=engine) as session:
        results = session.query(TaskResultModel, TaskModel).filter(
            TaskResultModel.status == "done", TaskModel.id == TaskResultModel.task_id
        )

        if last_minutes is not None:
            results = results.filter(
                TaskResultModel.completed_at
                > (datetime.datetime.now() - datetime.timedelta(minutes=last_minutes))
            )
        results = results.all()

        metrics = {}

        for task_result, original_task in results:
            if task_result.device_id not in metrics:
                metrics[task_result.device_id] = {}
            if original_task.name == "Sense":
                parse_sense_result(metrics, task_result, original_task)
            if original_task.name == "Led On" or original_task.name == "Led Off":
                parse_led_result(metrics, task_result, original_task)

    return metrics


def handle_create_task(body):
    # Lista de dispositivos en los que se carga la tarea.
    devices_ids = body.get("device_ids")

    with Session(engine) as session:
        devices = session.query(DeviceModel)
        known_devices = list(x.name for x in devices)

    for id in devices_ids:
        if id not in known_devices:
            return "Invalid device id", 400

    if len(devices_ids) < 1:
        return "Must add at least one device Id", 400

    if not body.get("task_name") or not body.get("device_ids"):
        return "Invalid empty params", 400

    logger.info(f'Creando tarea {body.get("task_name")} para {devices_ids}')

    execution_type = (
        ExecutionType.periodic if body.get("periodic") else ExecutionType.once
    )

    task_params = {}
    if body.get("task_params") is not None:
        task_params = body.get("task_params")

    task = TaskModel(
        name=body.get("task_name"),
        execution_type=execution_type,
        task_params=task_params,
    )

    with Session(engine) as session:
        session.add(task)
        session.commit()  # Need to commit to link by task.id
        task_results = [
            TaskResultModel(task_id=task.id, device_id=device_id)
            for device_id in devices_ids
        ]

        session.add_all(task_results)
        session.commit()

    return make_response("Created OK", 201)


def handle_remove_task(body):
    with Session(engine) as session:
        session.query(TaskModel).filter(TaskModel.id == body.get("id")).delete()
        session.commit()
    return make_response("Deleted OK", 200)


def handle_modify_task(body):
    with Session(engine) as session:
        session.query(TaskModel).filter(TaskModel.id == body.get("id")).update(
            {"status": body.get("status")}
        )
        session.commit()
    return make_response("Modified OK", 200)


# DTOs para las clases


def normalize_task_result(r: TaskResultModel):
    return {"id": r.id, "value": r.value, "device_id": r.device_id, "status": r.status}


def normalize_task(task: TaskModel):
    return {
        "id": task.id,
        "name": task.name,
        "execution_type": task.execution_type,
        "results": [normalize_task_result(r) for r in task.results],
        "status": task.status,
        "params": task.task_params,
        "created_at": task.created_at.isoformat(),
    }


# { device_id: <device_id>, task_name: <task_name>, perio}
def handle_get_active_tasks():

    f = TaskModel.status == TaskStatus.active

    with Session(engine) as s:
        tasks = [normalize_task(t) for t in s.query(TaskModel).filter(f)]

        logger.info(f"Devolviendo: {len(tasks)} tareas activas")

        response = []

        for t in tasks:
            for r in t["results"]:
                is_pending = r["status"] == ResultStatus.pending
                is_not_supported = r["status"] == ResultStatus.not_supported
                if is_pending or is_not_supported :
                    response.append(
                        {
                            "id": t["id"],
                            "task_name": t["name"],
                            "task_created_at": t["created_at"],
                            "device_id": r["device_id"],
                            "status": t["status"] if is_pending else "not_supported",
                            "execution_type": t["execution_type"],
                            "params": t["params"],
                        }
                    )

        return make_response(jsonify(response))


api_blueprint = Blueprint("api", __name__)


@api_blueprint.route("/measurements", methods=["GET"])
def get_measures():
    measurements = build_measurements(request.args)
    return make_response(jsonify(measurements), 200)


@api_blueprint.route("/task", methods=["POST", "DELETE", "PATCH", "GET"])
def task():
    try:
        body = json.loads(request.data) if request.data else {}

        if request.method == "POST":
            return handle_create_task(body)

        if request.method == "DELETE":
            return handle_remove_task(body)

        if request.method == "PATCH":
            return handle_modify_task(body)

        if request.method == "GET":
            return handle_get_active_tasks()

    except RuntimeError:
        return make_response("Invalid params", 400)


@api_blueprint.route("/devices/<device_id>", methods=["POST", "DELETE"])
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


@api_blueprint.route("/devices", methods=["GET"])
def devices_get_all_endpoint():
    if request.method == 'GET':
        with Session(engine) as session:
            devices = session.query(DeviceModel)
            return {
                'devices': list({"id": x.name} for x in devices)
            }, 200
