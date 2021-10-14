import io
import json
import time
from threading import Condition
from concurrent.futures import ProcessPoolExecutor

import cherrypy
from PIL import Image
import RPi.GPIO as GPIO
from picamerax import PiCamera
import piplates.MOTORplate as MOTOR

from ambvis.config import cfg
from ambvis.logger import log, debug

GPIO.setmode(GPIO.BCM)


def _rgb_to_image(data, filename):
    try:
        im = Image.frombytes('RGB', (4064, 3040), data)
        im.save(filename)
    except Exception as e:
        log('Unable to save image ' + filename + ': ' + str(e))


def update_websocket():
    status = {'led': int(led.on),
              'position': motor._position,
              'streaming': int(cam.streaming)}
    cherrypy.engine.publish('websocket-broadcast', json.dumps(status))


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\x00\x00\x00\x01'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            with self.condition:
                self.buffer.seek(0)
                self.frame = self.buffer.read()
                self.buffer.seek(0)
                self.buffer.truncate()
                self.condition.notify_all()
        return self.buffer.write(buf)


class Camera(object):
    def __init__(self):
        self.camera = PiCamera(resolution=(4056, 3040))
        self._streaming = False
        self.still_output = io.BytesIO()
        self.streaming_output = StreamingOutput()
        self.executor = ProcessPoolExecutor(max_workers=3)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.camera.close()
        self.executor.shutdown(wait=True)

    @property
    def streaming(self):
        return self._streaming
    
    @streaming.setter
    def streaming(self, val):
        if self._streaming != val:
            if not self._streaming:
                self.camera.resolution = (1280, 720)
                self.camera.start_recording(self.streaming_output, format='h264', profile='baseline', resize=(1280, 720))
                self._streaming = True
            else:
                self.camera.stop_recording()
                self.camera.resolution = (4056, 3040)
                self._streaming = False

    @property
    def image(self):
        if not self._streaming:
            self.still_output.seek(0)
            self.still_output.truncate()
            self.camera.capture(self.still_output, format="png")
            self.still_output.seek(0)
            return self.still_output

    def fast_capture(self, filename):
        stream = io.BytesIO()
        self.camera.capture(stream, format='rgb')
        stream.seek(0)
        self.executor.submit(_rgb_to_image, data=stream.read(), filename=filename)


class MotorError(Exception):
    pass


class Motor(object):
    def __init__(self):
        self._position = None
        self.hw = MOTOR
        self.reset()
        self.hw.enablestepSTOPint(0, 'A')
        self._direction = 'CW'
        self._accel = 2
        self._speed = 400
        self._powered = False
        # set up motor to run clockwise, with 8 microstep resolution,
        # turning 1600 steps per second (corresponding to 1 mm on the screw),
        # using 2 seconds to accellerate to the maximum speed.
        self.stepper_config()

    def reset(self):
        self.hw.RESET(0)
        self._powered = False

    def close(self):
        self.reset()

    def find_home(self):
        oldspeed = self._speed
        oldaccel = self._accel

        # first, back off 2 mm to clear the endstop
        # the state of the endstop cannot be reliably read via the interrupt registers
        self.stepper_config(dir='CCW', speed=1600)
        self.hw.stepperMOVE(0, 'A', 200)

        time.sleep(1) # give the motorplate time to cool down or it will not respon d to further commands

        # set motor to slow speed, short accel, and start turning
        self.stepper_config(dir='CW', speed=200, accelleration=0.2)
        self.hw.stepperJOG(0, 'A')
        timer = 0
        interrupted = 0
        _ = self.hw.getINTflag0(0) # clear interrupts
        while timer < 6000: # one minute timeout
            interrupted = self.hw.getINTflag0(0) & 0x8
            if interrupted:
                break
            time.sleep(0.01)
            timer += 1

        self.hw.stepperSTOP(0, 'A')
        self.stepper_config(dir='CW', speed=oldspeed, accelleration=oldaccel)
        self.hw.getINTflag0(0)

        if interrupted:
            self._position = 0
        else:
            print('fail')
            self._position = None
            raise MotorError('Timeout while finding home position')

    def move(self, val, type='abs'):
        if self._position is None:
            raise MotorError('Motor not homed.')

        if type == 'abs':
            steps = val - self._position
            if val < 0:
                raise MotorError('Will not move outside allowed range')
        elif type == 'rel':
            steps = val
            if self._position + steps < 0:
                raise MotorError('Will not move outside allowed range')
        else:
            raise MotorError('Move type must be either "abs" or "rel"')

        if steps > 0:
            self.direction = 'CCW'
        elif steps == 0:
            return
        else:
            self.direction = 'CW'

        self.hw.stepperMOVE(0, 'A', abs(steps))
        _ = self.hw.getINTflag0(0)
        while not self.hw.getINTflag0(0) & 0x20:
            time.sleep(0.1)

        self._position = self._position + steps

    def stepper_config(self, addr=0, motor='A', dir='NA', resolution=0, speed='NA', accelleration='NA'):
        '''configures stepper motor and saves values for future reference.'''
        self._direction = self._direction if dir == 'NA' else dir
        self._speed = self._speed if speed == 'NA' else speed
        self._accel = self._accel if accelleration == 'NA' else accelleration
        self._powered = True
        self.hw.stepperCONFIG(addr=addr, motor=motor, dir=self._direction, resolution=resolution,
                              rate=self._speed, acceleration=self._accel)

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, newdir):
        if newdir in ['CW', 'CCW']:
            self.stepper_config(dir=newdir)

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, val):
        self.stepper_config(speed=val)

    @property
    def homed(self):
        return True if self._position is not None else False

    @property
    def powered(self):
        return self._powered

    @powered.setter
    def powered(self, val):
        if val in [True, False] and val != self._powered:
            if val:
                self.stepper_config()
            else:
                self.hw.stepperOFF(0, 'A')
                self._powered = False

    @property
    def position(self):
        return self._position


class LEDController:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.pin = cfg.get('led_pin')
        GPIO.setup(self.pin, GPIO.OUT)
        self.on = False

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, val):
        if val in [True, False]:
            GPIO.output(self.pin, int(val))
            self._on = val


cam = Camera()
motor = Motor()
led = LEDController()
