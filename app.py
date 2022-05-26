import sys
import os
import json
import logging
import random

from flask import Flask, request, make_response, jsonify

app = Flask(__name__)

logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


LED_ON_TASK = {'name': 'led_on', 'config': {}}
LED_OFF_TASK = {'name': 'led_off', 'config': {}}
READ_INPUT = {'name': 'read', 'config': {}}


# Esto esta bastante mal Flask maneja workers
# que `pueden` acceder concurrentemente a este dict.

# TODO: usar db real

db = {}

@app.route('/')
def hello():
    return 'Hello world'

@app.route('/measurements', methods=['GET'])
def get_measures():
    return make_response(jsonify(db), 200)

@app.route('/tasks/<device_id>', methods=['GET', 'POST'])
def get_tasks(device_id):
    if request.method == 'POST':

        logger.info(f'Adding new entry for device id: {device_id}')

        # Es un resultado de alguna tarea
        tasks_results = json.loads(request.data)

        for result in tasks_results:
            task_name, task_result = result['name'], result['value']

            device_results = db.get(device_id, {})
            device_results[task_name] = task_result

            db[device_id] = device_results

        return make_response(jsonify([]), 200)

    else:
        tasks = [
            READ_INPUT,
            LED_ON_TASK if random.getrandbits(1) else LED_OFF_TASK
        ]
        return make_response(jsonify(tasks=tasks), 200)

if __name__ == '__main__':
    port = os.environ.get('PORT', 12345)
    print(f'Starting at port: {port}')

    app.run(port=port)
