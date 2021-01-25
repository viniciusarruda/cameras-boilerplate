import cv2
from multiprocessing import Process


class ConsumerExampleA(Process):

    def __init__(self, param, conn):
        super().__init__()

        self.conn = conn
        self.param = param

    def process(self, frame_id: int, camera_id: int, frame):

        cv2.imwrite(f'frame{self.param}.jpg', frame)
        return f'example{self.param}'

    def run(self):

        while True:

            frame_id, camera_id, frame = self.conn.recv()

            ret = self.process(frame_id, camera_id, frame)

            self.conn.send(ret)

