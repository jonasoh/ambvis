from threading import Thread
import cherrypy

class Broadcaster(Thread):
    def __init__(self, camera):
        super(Broadcaster, self).__init__()
        self.cam = camera

    def run(self):
        while True:
            with self.cam.streaming_output.condition:
                self.cam.streaming_output.condition.wait()
                cherrypy.engine.publish('websocket-broadcast', self.cam.streaming_output.frame, binary=True)
