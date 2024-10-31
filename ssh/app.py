# coding: utf-8
from flask import Flask

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def hello():
        print('app.py通過')
        return "Hello, World!"

    return app