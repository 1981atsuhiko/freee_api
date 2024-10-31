#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import cgitb
cgitb.enable()

import os
from wsgiref.handlers import CGIHandler
from sys import path
from flask import Flask

# Flaskアプリケーションのパスを設定
path.insert(0, '/home/bss/www/freee_api/')

def create_app():
    app = Flask(__name__)
    return app

try:
    from __init__ import create_app
    app = create_app()
except Exception as e:
    print(f"Error creating app: {e}")
    raise

class ProxyFix(object):
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        # 環境変数を設定
        try:
            environ['SERVER_NAME'] = "employee-master.bss-j.co.jp"  # ドメイン名を設定
            environ['SERVER_PORT'] = "80"
            environ['REQUEST_METHOD'] = environ.get('REQUEST_METHOD', 'GET')
            environ['SCRIPT_NAME'] = ""
            environ['PATH_INFO'] = environ.get('PATH_INFO', '/')
            environ['QUERY_STRING'] = environ.get('QUERY_STRING', '')
            environ['SERVER_PROTOCOL'] = "HTTP/1.1"
        except Exception as e:
            print(f"Error setting environment variables: {e}")
            raise
        return self.app(environ, start_response)

if __name__ == '__main__':
    try:
        app.wsgi_app = ProxyFix(app.wsgi_app)
        CGIHandler().run(app)
    except Exception as e:
        print(f"Error running CGIHandler: {e}")
        raise