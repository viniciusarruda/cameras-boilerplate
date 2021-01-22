import cv2
import time

# ~30 FPS
class FPS:

    def __init__(self):

        self.start_time = None
        self.fps = None

    def tick(self):
        self.start_time = time.time()

    def tack(self):
        self.fps = 1.0 / (time.time() - self.start_time)


class ConsumerExampleA:

    def __init__(self, queue):
        super().__init__()

        self.fps = FPS()
        self.queue = queue

        self.consume()

    def process(self, frame_id: int, camera_id: int, frame):

        cv2.imwrite('frame.jpg', frame)

    def consume(self):

        while True:

            self.fps.tick()

            frame_id, camera_id, frame = self.queue.get()

            self.process(frame_id, camera_id, frame)

            self.fps.tack()
            print('FPS: ', self.fps.fps)
