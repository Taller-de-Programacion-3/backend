import os
import logging

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from devices import devices_blueprint
from api import api_blueprint

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

app.register_blueprint(devices_blueprint, url_prefix="/devices")
app.register_blueprint(api_blueprint, url_prefix="/api")

# Configuramos el logger.

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
logger = logging.getLogger()

# Seteamos el logger de CORS en debug.
# logging.getLogger('flask_cors').level = logging.DEBUG

# Cargamos las variables de entorno.

load_dotenv()


@app.route("/")
def hello():
    return "Welcome to the Taller 3 API!"


if __name__ == "__main__":
    port = os.environ.get("PORT", 12345)
    print(f"Starting at port: {port}")

    app.run(port=port)
