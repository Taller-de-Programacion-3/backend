import json
import logging
import datetime
import sqlalchemy as sa

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
    ResultStatus,
    DeviceModel,
    DeviceStatus,
)

KNOWN_DEVICES_ID = ["esp32", "riscv", "argon", "test"]

logger = logging.getLogger()


def parse_led_result(metrics, task_result, task, device):
    result = metrics[device.name]

    if "led" not in result:
        result["led"] = {}
    if "on" not in result["led"]:
        result["led"]["on"] = []

    result["led"]["on"].append(
        {
            "value": 1 if task.name == "Led On" else 0,
            "timestamp": task_result.completed_at
        }
    )


def parse_sense_result(metrics, task_result, task, device):
    metric = task.task_params["sense_metric"]
    task_id = "Task ID: {}".format(task.id)

    result = metrics[device.name]

    if metric not in result:
        result[metric] = {}
    if task_id not in result[metric]:
        result[metric][task_id] = []

    result[metric][task_id].append(
        {
            "value": task_result.value,
            "timestamp": task_result.completed_at,
        }
    )


def build_measurements(args):
    last_minutes = None
    if "last" in args:
        last_minutes = int(args.get("last"))

    with Session(bind=engine) as session:
        results = session.query(TaskResultModel, TaskModel, DeviceModel).filter(
            TaskResultModel.status == ResultStatus.done,
            TaskModel.id == TaskResultModel.task_id,
            DeviceModel.id == TaskResultModel.device_id,
            DeviceModel.status == DeviceStatus.active
        )

        if last_minutes is not None:
            results = results.filter(
                TaskResultModel.completed_at
                > (datetime.datetime.now() - datetime.timedelta(minutes=last_minutes))
            )
        results = results.all()

        metrics = {}

        for task_result, original_task, device in results:
            if device.name not in metrics:
                metrics[device.name] = {}
            if original_task.name == "Sense":
                parse_sense_result(metrics, task_result, original_task, device)
            if original_task.name == "Led On" or original_task.name == "Led Off":
                parse_led_result(metrics, task_result, original_task, device)

    return metrics


def handle_create_task(body):

    # Lista de dispositivos en los que se carga la tarea.
    devices_keys = body.get("device_ids")

    with Session(engine) as session:
        devices = session.query(DeviceModel)
        known_devices = list(x.key for x in devices)

    for k in devices_keys:
        if k not in known_devices:
            return "Invalid device ID", 400

    if len(devices_keys) < 1:
        return "Must add at least one device ID", 400

    if not body.get("task_name") or not body.get("device_ids"):
        return "Invalid empty params", 400

    logger.info(f'Creando tarea {body.get("task_name")} para {devices_keys}')

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

        for key in devices_keys:
            target_device = [x for x in session.query(DeviceModel).filter(DeviceModel.key == key)]

            # Siempre deberia haber un solo dispositivo.
            result = TaskResultModel(task_id=task.id, device_id=target_device[0].id)

            session.add(result)

        session.commit()

    return make_response("Created OK", 201)


def handle_remove_task(body):

    logger.info(f"Marcando tarea como inactiva {body.get('id')}")

    with Session(engine) as session:
        (session.query(TaskModel)
                .filter(TaskModel.id == body.get("id"))
                .update({"status": TaskStatus.inactive }))

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
    return {
        "id": r.id,
        "value": r.value,
        "device_key": r.device.key,
        "device_status": r.device.status,
        "device_name": r.device.name,
        "status": r.status
    }


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


# { device_id: <device_id>, task_name: <task_name>, perio... }
def handle_get_active_tasks():

    f = TaskModel.status == TaskStatus.active

    with Session(engine) as s:
        tasks = [normalize_task(t) for t in s.query(TaskModel).filter(f)]

        logger.info(f"Devolviendo: {len(tasks)} tareas")

        response = []

        for t in tasks:
            for r in t["results"]:

                is_pending = r["status"] == ResultStatus.pending
                is_not_supported = r["status"] == ResultStatus.not_supported
                device_is_active = r["device_status"] == DeviceStatus.active

                if (is_pending or is_not_supported) and device_is_active:
                    response.append(
                        {
                            "id": t["id"],
                            "task_name": t["name"],
                            "task_created_at": t["created_at"],
                            "device_id": r["device_key"],
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
            # TODO falta ver el caso en que nos crean una tarea
            # y el dispositivo se desactiva.
            return handle_create_task(body)

        if request.method == "DELETE":
            return handle_remove_task(body)

        if request.method == "PATCH":
            return handle_modify_task(body)

        if request.method == "GET":
            return handle_get_active_tasks()

    except RuntimeError:
        return make_response("Invalid params", 400)


@api_blueprint.route("/devices/<device_key>", methods=["POST", "DELETE"])
def devices_endpoint(device_key):

    body = json.loads(request.data) if request.data else {}

    if request.method == "POST":

        logger.info(f"Setting device with key {device_key} as active")

        name = body.get("name")

        with Session(engine) as session:

            target_device = (
                sa.select(DeviceModel)
                .where(DeviceModel.key == device_key)
            )

            results = session.execute(target_device).scalars().all()

            if results:
                (session.query(DeviceModel)
                    .filter(DeviceModel.key == device_key)
                    .update({ 'status': DeviceStatus.active }))
            else:
                session.add(DeviceModel(key=device_key, name=name))

            session.commit()
            return make_response("ok", 200)

    if request.method == "DELETE":

        # NUNCA eliminamos dispositivos de la base de datos
        # siempre los desactivamos.

        logger.info(f"Setting device with key {device_key} as inactive")

        with Session(engine) as session:

            (session.query(DeviceModel)
                .filter(DeviceModel.key == device_key)
                .update({ 'status': DeviceStatus.inactive }))

            session.commit()
        return make_response("Deleted OK", 200)


def build_device_data(device_model):
    return {
        "id": device_model.key,
        "name": device_model.name,
        "is_active": device_model.status == DeviceStatus.active
    }


@api_blueprint.route("/devices", methods=["GET"])
def get_devices():
    with Session(engine) as session:
        devices = session.query(DeviceModel)
        return make_response({"devices": [build_device_data(d) for d in devices]}, 200)
