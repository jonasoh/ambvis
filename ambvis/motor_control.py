from flask import Blueprint, Response, request, abort, session, redirect, url_for, flash, render_template

from ambvis import globals
from ambvis.hw import motor, MotorError
from ambvis.config import Config
from ambvis.logger import log, debug
from ambvis.decorators import public_route

cfg = Config()
bp = Blueprint('motor_control', __name__, url_prefix='/motor')

@bp.route('/move/home')
def find_home():
    motor.find_home()
    return Response('OK', 200)

@bp.route('/move/<string:type>/<string:val>')
def move(type, val):
    val = int(val)
    if type in ['abs', 'rel'] and val is not None:
        try:
            motor.move(val, type)
            return Response('OK', 200)
        except MotorError as e:
            return Response(str(e), 500)
    else:
        abort(404)

@bp.route('/status/homed')
def homed():
    return Response(str(motor.homed), 200)

@bp.route('/status/powered')
def powered():
    return Response(str(motor.powered), 200)

@bp.route('/power/<val>')
def power(val):
    val = val.lower()
    if val in ['on', 'off']:
        if val == 'on':
            motor.powered = True
        else:
            motor.powered = False
    else:
        abort(404)
    return Response('OK', 200)
