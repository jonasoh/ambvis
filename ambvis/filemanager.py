import os
import shutil
import subprocess

from flask import Blueprint, Response, request, abort, redirect, url_for, flash, render_template

from ambvis.config import cfg

bp = Blueprint('filemanager', __name__, url_prefix='/files')


def stream_popen(p):
    '''generator for sending STDOUT to a web client'''
    data = p.stdout.read(128*1024)
    while data:
        yield data
        data = p.stdout.read(128*1024)


def verify_dir(check_dir):
    '''checks that the directory is
       1. immediately contained within the appropriate parent dir
       2. does not contain initial dots, and
       3. is indeed a directory'''
    check_dir = os.path.abspath(check_dir)
    dir = os.path.expanduser('~')
    return os.path.dirname(check_dir) == dir and not os.path.basename(check_dir).startswith('.') and os.path.isdir(check_dir)


@bp.route('/')
def file_browser():
    dirs = []
    dir = os.path.expanduser('~')
    df = shutil.disk_usage(dir)
    diskspace = round(df.free / 1024 ** 3, 1)

    for entry in os.scandir(dir):
        if entry.is_dir() and os.path.dirname(entry.path) == dir and not entry.name.startswith('.'):
            dirs.append(entry.name)
    return render_template('filemanager.jinja', dirs=sorted(dirs), diskspace=diskspace, name=cfg.get('name'))

@bp.route('/get/<exp_dir>.zip')
def make_zipfile(exp_dir):
    'creates a zipfile on the fly, and streams it to the client'
    dir = os.path.expanduser('~')
    zip_dir = os.path.abspath(os.path.join(dir, exp_dir))
    if verify_dir(zip_dir):
        p = subprocess.Popen(['/usr/bin/zip', '-r', '-0', '-',
                             os.path.basename(zip_dir)], stdout=subprocess.PIPE, cwd=dir)
        return Response(stream_popen(p), mimetype='application/zip')
    else:
        abort(404)


@bp.route('/delete/<exp_dir>/', methods=['GET', 'POST'])
def delete_dir(exp_dir):
    dir = os.path.expanduser('~')
    del_dir = os.path.abspath(os.path.join(dir, exp_dir))

    if request.method == 'GET':
        return render_template('delete.html', dir=exp_dir)
    else:
        #if os.path.abspath(experimenter.dir) == del_dir and experimenter.running:
        #    flash(
        #        'Cannot remove active experiment directory. Please stop experiment first.')
        #    return redirect(url_for('file_browser'))
        if verify_dir(del_dir):
            shutil.rmtree(del_dir)
            flash(f'Directory {exp_dir} deleted.')
            return redirect(url_for('file_browser'))
        else:
            flash(f'Unable to delete directory "{exp_dir}".')
            return redirect(url_for('file_browser'))

