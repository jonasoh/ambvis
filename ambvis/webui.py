import os
import hashlib
import subprocess
from threading import Timer

import cherrypy
from ws4py.websocket import WebSocket
from wsgiref.simple_server import make_server
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from flask import Flask, Response, request, abort, flash, redirect, url_for, render_template, session

from ambvis import auth
from ambvis import motor_control
from ambvis.hw import cam, motor
from ambvis.config import cfg
from ambvis import filemanager
from ambvis.logger import log, debug
from ambvis.video_stream import Broadcaster
from ambvis.decorators import public_route, not_while_running

def create_app():
    app = Flask(__name__)
    if cfg.get('secret') == '':
        secret = hashlib.sha1(os.urandom(16))
        cfg.set('secret', secret.hexdigest())
    app.config.update(
        SECRET_KEY=cfg.get('secret')
    )
    app.register_blueprint(auth.bp)
    app.register_blueprint(filemanager.bp)
    app.register_blueprint(motor_control.bp)
    return app

app = create_app()
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool()


@app.route('/index.html')
@app.route('/')
def index():
    return render_template('index.jinja')

def run():
    cam.streaming = True
    broadcast_thread = Broadcaster(camera=cam)
    try:
        #app.run(host="0.0.0.0", port=8080)
        broadcast_thread.daemon = True
        broadcast_thread.start()
        cherrypy.tree.graft(app, '/')
        cherrypy.tree.mount(WebSocketRoot, '/video', config={'/frame': {'tools.websocket.on': True, 'tools.websocket.handler_cls': StreamingWebSocket}})
        cherrypy.server.bind_addr = ('0.0.0.0', 8080)
        cherrypy.engine.start()
        cherrypy.engine.block()
    finally:
        cam.close()
        motor.close()


@app.route('/still.png')
def get_image():
    return Response(cam.image, mimetype='image/png')


def run_shutdown():
    subprocess.run(['sudo', 'shutdown', '-h', 'now'])

@not_while_running
@app.route('/shutdown')
def shutdown():
    t = Timer(1, run_shutdown)
    t.start()
    return render_template('shutdown.jinja', message='Shutting down', refresh=0, longmessage="Allow the shutdown process to finish before turning the power off.")


def run_reboot():
    subprocess.run(['sudo', 'shutdown', '-r', 'now'])


@not_while_running
@app.route('/reboot')
def reboot():
    t = Timer(1, run_reboot)
    t.start()
    return render_template('shutdown.jinja', message='Rebooting', refresh=120, longmessage='Please allow up to two minutes for system to return to usable state.')


def run_restart():
    cherrypy.engine.restart()


@not_while_running
@app.route('/restart')
def restart():
    t = Timer(1, run_restart)
    t.start()
    return render_template('shutdown.jinja', message='Restarting web UI', refresh=15, longmessage='Please allow up to 15 seconds for the web UI to restart.')


class StreamingWebSocket(WebSocket):
    def opened(self):
        print("New client connected")


class WebSocketRoot:
    @cherrypy.expose
    def index():
        pass
    
    @cherrypy.expose
    def frame():
        pass
