import sys
import os
import random
import logging

from flask import Flask
from devices import devices_blueprint
from api import api_blueprint


from datamodel import engine
app = Flask(__name__)
app.register_blueprint(devices_blueprint, url_prefix='/devices')
app.register_blueprint(api_blueprint, url_prefix='/api')

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()

@app.route('/')
def hello():
    with engine.connect() as con:
        query_result = con.execute('SELECT * FROM tasks')

        for row in query_result:
            print(row)

    return 'Hello world'


if __name__ == '__main__':
    port = os.environ.get('PORT', 12345)
    print(f'Starting at port: {port}')

    app.run(port=port)
