import os

from PIL import Image
from flask import Blueprint, Response, request, abort, session, redirect, url_for, flash, render_template

from ambvis import globals
from ambvis.hw import motor, led, cam
from ambvis.config import Config
from ambvis.logger import log, debug
from ambvis.decorators import not_while_running, public_route

cfg = Config()
bp = Blueprint('imaging_settings', __name__, url_prefix='/settings/imaging')


@not_while_running
@bp.route('/')
def settings():
    return render_template('imaging_settings.jinja', led=led.on, position=motor._position, positions=cfg.get('positions'))


@not_while_running
@bp.route('/save_pos')
def save_pos():
    saved_pos = cfg.get('positions')
    if motor.position in saved_pos:
        flash('Position already saved.')
        return redirect(url_for('.settings'))
    
    prev_led = led.on
    led.on = True
    cam.streaming = False
    cam.camera.resolution = (1024, 768)
    thumb = Image.open(cam.image).convert('RGB')
    led.on = prev_led
    cam.streaming = True
    thumb.save(os.path.join(cfg.cfgdir, 'thumb_' + str(motor.position) + '.jpg'))
    saved_pos.append(motor.position)
    cfg.set('positions', sorted(saved_pos))
    flash('Position saved.')
    return redirect(url_for('.settings'))

@not_while_running
@bp.route('/del_pos/<int:num>')
def del_pos(num):
    saved_pos = cfg.get('positions')
    if num in saved_pos:
        saved_pos.remove(num)
        flash('Position removed.')
    cfg.set('positions', saved_pos)
    return redirect(url_for('.settings'))


@bp.route('/thumb/<int:num>')
def get_thumb(num):
    thumbpath = os.path.join(cfg.cfgdir, 'thumb_' + str(num) + '.jpg')
    if os.path.exists(thumbpath):
        with open(thumbpath, 'rb') as f:
            return Response(f.read(), 200, mimetype='image/jpeg')
    else:
        abort(404)
