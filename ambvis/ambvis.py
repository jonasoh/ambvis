#!/usr/bin/env python3
# 
# ambvis.py -
#   control program for the AMBvis web interface

import os
import sys
import textwrap
import argparse

from ambvis import webui
from ambvis.config import cfg

parser = argparse.ArgumentParser(
    description=textwrap.dedent("""\
                                AMBvis control software.
                                Running this command without any flags starts the web interface.
                                Specifying flags will perform those actions, then exit."""))
parser.add_argument('--install-service', action="store_true", dest="install",
                    help="install systemd user service file")
parser.add_argument('--reset-config', action="store_true", dest="reset",
                    help="reset all configuration values to defaults")
parser.add_argument('--reset-password', action="store_true", dest="resetpw",
                    help="reset web UI password")
parser.add_argument('--toggle-debug', action="store_true", dest="toggle_debug",
                    help="toggles additional debug logging on or off")
options = parser.parse_args()


def install_service():
    try:
        os.makedirs(os.path.expanduser('~/.config/systemd/user'), exist_ok=True)
    except OSError as e:
        print("Could not make directory (~/.config/systemd/user):", e)
    try:
        with open(os.path.expanduser('~/.config/systemd/user/ambvis.service'), 'w') as f:
            if (os.path.exists('/home/pi/.local/bin/ambvis')):
                exe = '/home/pi/.local/bin/ambvis'
            else:
                exe = '/usr/local/bin/ambvis'
            f.write(textwrap.dedent("""\
                [Unit]
                Description=AMBvis control software
                [Service]
                ExecStart={}
                Restart=always
                [Install]
                WantedBy=default.target
                """).format(exe))
    except OSError as e:
        print("Could not write file (~/.config/systemd/user/ambvis.service):", e)
    print("Systemd service file installed.")

def main():
    if options.reset:
        print("Clearing all configuration values.")
        try:
            os.remove(os.path.expanduser('~/.config/ambvis/spiro.conf'))
        except OSError as e:
            print("Could not remove file ~/.config/ambvis/spiro.conf:", e.strerror)
            raise
    if options.install:
        print("Installing systemd service file.")
        install_service()
    if options.resetpw:
        print("Resetting web UI password.")
        cfg.set('password', '')
    if options.toggle_debug:
        cfg.set('debug', not cfg.get('debug'))
        if cfg.get('debug'):
            print("Debug mode on.")
        else:
            print("Debug mode off")

    if any([options.install, options.resetpw, options.toggle_debug]):
        sys.exit()

    webui.run()
