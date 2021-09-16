import io
from threading import Condition

import RPi.GPIO as GPIO
from picamerax import PiCamera
import piplates.MOTORplate as M

from ambvis.config import cfg


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
        self.camera = PiCamera()
        self._streaming = False
        self.still_output = io.BytesIO()
        self.streaming_output = StreamingOutput()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.camera.close()

    @property
    def streaming(self):
        return self._streaming
    
    @streaming.setter
    def streaming(self, val):
        if self._streaming != val:
            if not self._streaming:
                self.camera.start_recording(self.streaming_output, format='h264', profile='baseline', resize=(1280, 720))
                self._streaming = True
            else:
                self.camera.stop_recording()
                self._streaming = False

    @property
    def image(self):
        if not self._streaming:
            self.still_output.truncate()
            self.still_output.seek(0)
            self.camera.capture(self.still_output, format="png")
            self.still_output.seek(0)
            return self.still_output


class Motor(object):
    def __init__(self):
        self.position = None
        GPIO.setmode(GPIO.BCM)

    def find_home(self):
        pass


cam = Camera()
motor = Motor()
