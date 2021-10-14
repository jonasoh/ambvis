import os
import time
import hashlib
import subprocess
from threading import Timer, Thread

import cherrypy
from cherrypy.process.plugins import Daemonizer
from werkzeug import datastructures
from ws4py.websocket import WebSocket
from wsgiref.simple_server import make_server
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from flask import Flask, Response, request, abort, flash, redirect, url_for, render_template, session

from ambvis import auth
from ambvis import motor_control
from ambvis.hw import cam, motor, led, update_websocket
from ambvis.config import cfg
from ambvis import filemanager
from ambvis import system_settings
from ambvis import imaging_settings
from ambvis.logger import log, debug
from ambvis.video_stream import Broadcaster
from ambvis.experimenter import Experimenter
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
    app.register_blueprint(system_settings.bp)
    app.register_blueprint(imaging_settings.bp)
    return app


app = create_app()
experimenter = Experimenter()
experimenter.daemon = True
experimenter.start()
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

WebSocketPlugin(cherrypy.engine).subscribe()
cherrypy.tools.websocket = WebSocketTool()


def run():
    '''start web ui and initialize hardware peripherals'''
    log('Initializing hardware...')
    # flash led to show it is working
    led.on = True
    time.sleep(1)
    led.on = False

    # home the motor
    motor.find_home()

    cam.streaming = True
    ws_t = Thread(target=continuously_update_websocket, daemon=True)
    ws_t.start()
    broadcast_thread = Broadcaster(camera=cam)
    try:
        #app.run(host="0.0.0.0", port=8080)
        broadcast_thread.daemon = True
        broadcast_thread.start()
        cherrypy.tree.graft(app, '/')
        cherrypy.tree.mount(StreamingWebSocketRoot, '/video', config={'/frame': {'tools.websocket.on': True, 'tools.websocket.handler_cls': StreamingWebSocket}})
        cherrypy.tree.mount(StatusWebSocketRoot, '/api', config={'/ws': {'tools.websocket.on': True, 'tools.websocket.handler_cls': StatusWebSocket}})
        cherrypy.server.bind_addr = ('0.0.0.0', 8080)
        cherrypy.engine.start()
        cherrypy.engine.block()
    finally:
        experimenter.stop_experiment = experimenter.quit = True
        cam.close()
        motor.close()
        led.on = False


@app.route('/index.html')
@app.route('/')
def index():
    if experimenter.running:
        return redirect(url_for('experiment'))
    else:
        return render_template('index.jinja')


@app.route('/still.png')
def get_image():
    return Response(cam.image.read(), mimetype='image/png')


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


@not_while_running
@app.route('/led/<val>')
def set_led(val):
    if val in ['on', 'off']:
        if val == 'on':
            led.on = True
        else:
            led.on = False
        return Response('OK', 200)
    abort(404)


@app.route('/experiment', methods=['GET', 'POST'])
def experiment():
    if request.method == 'GET':
        print(experimenter.running)
        return render_template('experiment.jinja', running=experimenter.running)
    else:
        if request.form['action'] == 'start':
            if request.form.get('expname') is None:
                expname = time.strftime("%Y-%m-%d Unnamed experiment", time.localtime())
            else:
                expname = request.form.ge('expname')
            experimenter.dir = os.path.join(os.path.expanduser('~'), expname)

            if request.form.get('imgfreq') is None:
                experimenter.imgfreq = 60
            else:
                experimenter.imgfreq = int(request.form.get('imgfreq'))

            experimenter.stop_experiment = False
            experimenter.status_change.set()
        elif request.form['action'] == 'stop':
            experimenter.stop_experiment = True

        time.sleep(0.5)
        return render_template('experiment.jinja', running=experimenter.running)
        

class StreamingWebSocket(WebSocket):
    '''the video streaming websocket broadcasts only binary data'''
    def opened(self):
        print("New video client connected")

    def send(self, payload, binary=False):
        if binary == True:
            super().send(payload, binary)


class StatusWebSocket(WebSocket):
    '''the status websocket only broadcasts non-binary data'''
    last_message = None

    def opened(self):
        print("New status client connected")

    def send(self, payload, binary=False):
        if binary == False:
            if payload != self.last_message:
                self.last_message = payload
                super().send(payload, binary)


class StreamingWebSocketRoot:
    @cherrypy.expose
    def index():
        pass
    
    @cherrypy.expose
    def frame():
        pass


class StatusWebSocketRoot:
    @cherrypy.expose
    def index():
        pass
    
    @cherrypy.expose
    def ws():
        pass


def continuously_update_websocket():
    '''send out a status message as json every second'''
    while True:
        update_websocket()
        time.sleep(1)
