import os
import time
import threading

from ambvis.config import cfg
from ambvis.logger import log, debug
from ambvis.hw import cam, motor, led

class Experimenter(threading.Thread):
    def __init__(self):
        self.cam = cam
        self.motor = motor
        self.led = led
        self.cfg = cfg
        self.dir = os.path.expanduser('~')
        self.imgfreq = 60
        self.status = 'Stopped'
        self.running = False
        self.stop_experiment = False
        self.status_change = threading.Event()
        self.quit = False
        super().__init__()

    def run(self):
        while not self.quit:
            self.status_change.wait()
            log('Status change')
            self.status_change.clear()
            self.run_experiment()

    def run_experiment(self):
        self.running = True
        os.makedirs(self.dir, exist_ok=True)
        saved_pos = cfg.get('positions')
        self.cam.streaming = False
        log('Starting experiment ' + os.path.basename(self.dir))

        while not self.stop_experiment:
            for pos in saved_pos:
                loopstart = time.time()
                if self.motor.position != pos: 
                    self.motor.move(pos)
                self.led.on = True
                time.sleep(1)
                now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                fname = os.path.join(self.dir, 'pos_' +
                                     str(pos) + '_' + now + '.png')
                cam.fast_capture(fname)
                self.led.on = False

            self.motor.move(saved_pos[0])

            time_taken = time.time() - loopstart
            time_left = self.imgfreq*60 - time_taken

            while time_left > 0 and not self.stop_experiment:
                time.sleep(time_left)
                time_taken = time.time() - loopstart
                time_left = self.imgfreq*60 - time_taken

        log('Experiment finished.')
        self.cam.streaming = True
        self.running = False
