import os
import sys
import json

def log(msg):
    sys.stderr.write(msg + '\n')
    sys.stderr.flush()


class Config(object):
    defaults = {
        'password': '',      # an empty password will trigger password initialization for web ui
        'secret': '',        # secret key for flask sessions
        'name': 'ambvis',    # the name of this ambvis instance
        'debug': True,       # debug logging
        'led_pin': 17,       # GPIO pin to use for LED control
    }

    config = {}

    def __init__(self):
        self.cfgdir = os.path.expanduser("~/.config/ambvis")
        self.cfgfile = os.path.join(self.cfgdir, "ambvis.conf")
        self.read()
        if os.path.exists(self.cfgfile):
            st = os.stat(self.cfgfile)
            self.mtime = st.st_mtime
        else:
            self.mtime = 0

    def read(self):
        os.makedirs(self.cfgdir, exist_ok=True)
        if os.path.exists(self.cfgfile):
            try:
                with open(self.cfgfile, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                log("Failed to read or parse config file: " + str(e))

    def write(self):
        try:
            with open(self.cfgfile + ".tmp", 'w') as f:
                json.dump(self.config, f, indent=4)
            os.replace(self.cfgfile + ".tmp", self.cfgfile)
        except OSError as e:
            log("Failed to write config file: " + e.strerror)

    def get(self, key):
        if os.path.exists(self.cfgfile):
            st = os.stat(self.cfgfile)
            mt = st.st_mtime
            if mt > self.mtime:
                # config file was changed on disk -- reload it
                self.read()

        return self.config.get(key, self.defaults.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.write()

    def unset(self, key):
        if key in self.config:
            del self.config[key]
            self.write()


cfg = Config()
