#!/usr/bin/env python3

from flask import Flask, request, Response, render_template
from waitress import serve

import traceback, json

app = Flask('linux-struct-db')

@app.route('/', defaults = {'path' : ''}, methods = ['GET'])
@app.route('/<path:path>', methods = ['GET'])
def main(path):
    return render_template('index.html')

@app.after_request
def afterRequest(response):
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = "nosniff"
    response.headers['X-Powered-By'] = 'Arch Linux'
    response.headers['Server'] = 'linux struct db'

    return response


if __name__ == '__main__':
    serve(app, host = '127.0.0.1', port = 5000, threads = 8)
