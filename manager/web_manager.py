from os.path import join

from flask import Flask, send_file
from flask_cors import CORS

web_app = Flask(__name__, template_folder='../templates/')
# logging.getLogger('werkzeug').setLevel(logging.ERROR)
CORS(web_app)


@web_app.route('/src/<path:path>')
def src(path: str):
    return send_file(join('../templates/src', path))


def start():
    web_app.run(host='0.0.0.0', port=80)
