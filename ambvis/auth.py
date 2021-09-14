import hashlib

from flask import Blueprint, request, abort, session, redirect, url_for, flash, render_template

import globals
from config import Config
from logger import log, debug
from decorators import public_route

cfg = Config()
bp = Blueprint('auth', __name__, url_prefix='/auth')


def check_pass(pwd):
    if pwd:
        hash = hashlib.sha1(pwd.encode('utf-8'))
        if hash.hexdigest() == cfg.get('password'):
            return True
    return False


@bp.before_app_request
def check_route_access():
    '''checks if access to a certain route is granted. allows anything going to /static/ or that is marked public.'''
    if not request.endpoint:
        abort(404)
    if cfg.get('password') == '' and not any([request.endpoint == 'auth.newpass', 
                                              request.endpoint == 'static',
                                              request.endpoint in globals.public_routes]):
        return redirect(url_for('auth.newpass'))
    if any([request.endpoint == 'static',
            check_pass(session.get('password')),
            request.endpoint in globals.public_routes]):
        #if experimenter.running and getattr(app.view_functions[request.endpoint], 'not_while_running', False):
        #    return redirect(url_for('empty'))
        return  # Access granted
    else:
        return redirect(url_for('auth.login'))


@public_route
@bp.route('/newpass', methods=['GET', 'POST'])
def newpass():
    if request.method == 'POST':
        currpass = request.form['currpass']
        pwd1 = request.form['pwd1']
        pwd2 = request.form['pwd2']

        if cfg.get('password') != '':
            if not check_pass(currpass):
                flash("Current password incorrect.")
                return render_template('newpass.jinja', name=cfg.get('name'))

        if pwd1 == pwd2:
            hash = hashlib.sha1(pwd1.encode('utf-8'))
            cfg.set('password', hash.hexdigest())
            session['password'] = pwd1
            flash("Password was changed.")
            log("Password was changed by user with IP " + request.remote_addr)
            return redirect(url_for('index'))
        else:
            flash("Passwords do not match.")
            log("Password change attempt failed by user with IP " + request.remote_addr)
            return redirect(url_for('auth.newpass'))
    else:
        return render_template('newpass.jinja', nopass=cfg.get('password') == '', name=cfg.get('name'))


@public_route
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pwd = request.form['password']
        if check_pass(pwd):
            session['password'] = pwd
            log("Web user successfully logged in from IP " + request.remote_addr)
            return redirect(url_for('index'))
        else:
            flash("Incorrect password.")
            log("Incorrect password in web login from IP " + request.remote_addr)
            return redirect(url_for('auth.login'))
    else:
        return render_template('login.jinja', name=cfg.get('name'))


@public_route
@bp.route('/logout')
def logout():
    session['password'] = ''
    return redirect(url_for('auth.login'))
