import sys
import os

from flask import Flask, request, make_response, jsonify
from random import getrandbits

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello world'

@app.route('/tasks/<device_id>', methods=['GET'])
def get_tasks(device_id):
    tasks = []
    if (bool(getrandbits(1))):
        tasks.append({ 'name': 'led_on', 'config': {} })
    else:
        tasks.append({ 'name': 'led_off', 'config': {} })
    return make_response(jsonify(tasks=tasks), 200)


if __name__ == '__main__':
    try:
        port = os.environ.get('PORT', 12345)
        print(f'Starting at port: {port}')
        app.run(port=port)
    except KeyError:
        app.run()
