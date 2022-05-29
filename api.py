from flask import Blueprint, make_response, jsonify
from db import db

api_blueprint = Blueprint('api', __name__)


@api_blueprint.route('/measurements', methods=['GET'])
def get_measures():
    return make_response(jsonify(db), 200)


@api_blueprint.route('/queue', methods=['POST'])
def queue_task():
    # Sin importar que nos llegue encolamos una read task en
    # cada dispositivo.

    # TODO

    return make_response('ok', 200)
