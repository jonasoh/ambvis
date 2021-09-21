from flask import Blueprint, Response, request, abort, session, redirect, url_for, flash, render_template

from ambvis import globals
from ambvis.hw import motor, MotorError
from ambvis.config import Config
from ambvis.logger import log, debug
from ambvis.decorators import public_route

cfg = Config()
bp = Blueprint('system_settings', __name__, url_prefix='/settings/system')


@bp.route('/')
def settings():
    return render_template('system_settings.jinja')
