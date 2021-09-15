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
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.buffer.seek(0)
                self.condition.notify_all()
        return self.buffer.write(buf)


class Camera(object):
    def __init__(self):
        self.camera = PiCamera()
        self._streaming = False
        self.still_output = io.BytesIO()
        self.streaming_output = StreamingOutput()

    @property
    def streaming(self):
        return self._streaming
    
    @streaming.setter
    def streaming(self, val):
        if self._streaming != val:
            if not self._streaming:
                self.camera.start_recording(self.streaming_output, format='mjpeg', resize='1024x768')
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

    @property
    def stream_generator(self):
        while True:
            with self.streaming_output.condition:
                got_frame = self.streaming_output.condition.wait(timeout=0.1)
            if got_frame:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + self.streaming_output.frame + b'\r\n')
            else:
                # failed to acquire an image; return nothing instead of waiting
                yield b''


class Motor(object):
    def __init__(self):
        self.position = None
        GPIO.setmode(GPIO.BCM)

    def find_home(self):
        pass


cam = Camera()
motor = Motor()

