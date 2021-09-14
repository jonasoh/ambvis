import os
import hashlib

from flask import Flask, request, abort, flash, redirect, url_for, render_template, session

import auth
import globals
from config import Config
from auth import check_pass
from logger import log, debug
from decorators import public_route, not_while_running

cfg = Config()


def create_app():
    app = Flask(__name__)
    if cfg.get('secret') == '':
        secret = hashlib.sha1(os.urandom(16))
        cfg.set('secret', secret.hexdigest())
    app.config.update(
        DEBUG=cfg.get('debug'),
        SECRET_KEY=cfg.get('secret')
    )
    app.register_blueprint(auth.bp)
    return app

app = create_app()


@app.route('/index.html')
@app.route('/')
def index():
    return render_template('index.jinja')


app.run(host="127.0.0.1", port=8080)
