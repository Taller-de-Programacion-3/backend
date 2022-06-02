import sys
import os
import logging
import random

from flask import Flask
from devices import devices_blueprint
from api import api_blueprint

app = Flask(__name__)

logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

app.register_blueprint(devices_blueprint, url_prefix='/devices')
app.register_blueprint(api_blueprint, url_prefix='/api')

@app.route('/')
def hello():
    return 'Hello world'


if __name__ == '__main__':
    port = os.environ.get('PORT', 12345)
    print(f'Starting at port: {port}')

    app.run(port=port)
