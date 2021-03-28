from threading import Thread

from flask import Flask
from flask_restful import Api


class Launcher:
    def __init__(self):
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.thread = Thread(target=self.run, kwargs={'debug': True})

        self.thread.setDaemon(True)

    def start(self):
        self.thread.start()

    def run(self, *args, **kwargs):
        self.app.run(*args, **kwargs)

    def load_resource(self, destination: str):
        exec(f'import {destination}')
        eval(f'{destination}.setup')(self.api)
