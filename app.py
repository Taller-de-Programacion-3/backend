import sys
import os
import logging
import random

from flask import Flask
from devices import devices_blueprint
from api import api_blueprint

from sqlalchemy import create_engine

db_url = os.environ.get('DB_URL')

app = Flask(__name__)

logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

app.register_blueprint(devices_blueprint, url_prefix='/devices')
app.register_blueprint(api_blueprint, url_prefix='/api')

engine = create_engine(db_url)

@app.route('/')
def hello():
    with engine.connect() as con:
        query_result = con.execute('SELECT * FROM tasks')

        for row in query_result:
            print('row')

    return 'Hello world'


if __name__ == '__main__':
    port = os.environ.get('PORT', 12345)
    print(f'Starting at port: {port}')

    app.run(port=port)
