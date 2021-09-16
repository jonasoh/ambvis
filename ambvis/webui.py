import os
import hashlib

from flask import Flask, Response, request, abort, flash, redirect, url_for, render_template, session

from ambvis import auth
from ambvis import globals
from ambvis.config import cfg
from ambvis.logger import log, debug
from ambvis.decorators import public_route, not_while_running

from ambvis.hw import cam

def create_app():
    app = Flask(__name__)
    if cfg.get('secret') == '':
        secret = hashlib.sha1(os.urandom(16))
        cfg.set('secret', secret.hexdigest())
    app.config.update(
        SECRET_KEY=cfg.get('secret')
    )
    app.register_blueprint(auth.bp)
    return app

app = create_app()


@app.route('/index.html')
@app.route('/')
def index():
    return render_template('index.jinja')

def run():
    cam.streaming = True
    app.run(host="0.0.0.0", port=8080)

@app.route('/stream.mjpg')
def live_stream():
    return Response(cam.stream_generator, mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/still.png')
def get_image():
    return Response(cam.image, mimetype='image/png')
