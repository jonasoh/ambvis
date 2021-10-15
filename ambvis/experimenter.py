import os
import time
import threading

from ambvis.config import cfg
from ambvis.logger import log, debug
from ambvis.hw import cam, motor, led


class Experimenter(threading.Thread):
    def __init__(self):
        self.cfg = cfg
        self.dir = os.path.expanduser('~')
        self.imgfreq = 60
        self.status = 'Stopped'
        self.running = False
        self.stop_experiment = False
        self.status_change = threading.Event()
        self.quit = False
        self.starttime = None
        super().__init__()

    def run(self):
        while not self.quit:
            self.status_change.wait()
            self.status_change.clear()
            self.run_experiment()

    def run_experiment(self):
        self.running = True
        os.makedirs(self.dir, exist_ok=True)
        saved_pos = cfg.get('positions')
        cam.streaming = False
        log('Starting experiment ' + os.path.basename(self.dir))
        self.starttime = time.strftime("%Y-%m-%d %H:%M", time.localtime())

        # fix AWB
        led.on = True
        cam.camera.awb_mode = "auto"
        time.sleep(3)
        g = cam.camera.awb_gains
        cam.camera.awb_mode = "off"
        cam.camera.awb_gains = g
        led.on = False

        while not self.stop_experiment:
            motor.find_home()
            for pos in saved_pos:
                loopstart = time.time()
                if motor.position != pos:
                    motor.move(pos)
                led.on = True
                time.sleep(1)
                now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                fname = os.path.join(self.dir, 'pos_' +
                                     str(pos) + '_' + now + '.png')
                cam.fast_capture(fname)
                led.on = False

            time_taken = time.time() - loopstart
            time_left = self.imgfreq*60 - time_taken

            while time_left > 0 and not self.stop_experiment:
                time.sleep(1)
                time_taken = time.time() - loopstart
                time_left = self.imgfreq*60 - time_taken

        log('Experiment finished.')
        cam.camera.awb_mode = "auto"
        cam.streaming = True
        self.running = False
