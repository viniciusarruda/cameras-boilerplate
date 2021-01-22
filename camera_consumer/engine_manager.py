import multiprocessing as mp
from camera import Camera
from consumer import ConsumerExampleA
import time


class EngineManager:

    def __init__(self):
        super().__init__()

        self.cameras = {}
        self.camera_id = 0

        self.queue = mp.Queue(maxsize=4)

        self.consumer_A = mp.Process(target=ConsumerExampleA, args=(self.queue,))
        self.consumer_A.start()

    def add_camera(self):

        print('AddCamera on Manager called')
        url = 'rtsp://Admin:1234@10.5.1.10:554/rtsp/profile1'
        camera_id = self.camera_id  # get from db after inserting it
        data = {'id': camera_id, 'url': url}

        terminate = mp.Value('B', 0)
        crop_roi = mp.Value('B', 0)
        width = mp.Value('I', 0)
        height = mp.Value('I', 0)
        x = mp.Value('I', 0)
        y = mp.Value('I', 0)
        camera_p = mp.Process(target=Camera, args=(data, {}, self.queue, False, terminate, crop_roi, width, height, x, y))  # colocar esses parametros em um dict
        # camera_p.daemon = True
        camera_p.start()

        self.cameras[camera_id] = (camera_p, terminate)
        self.camera_id += 1


if __name__ == "__main__":
    em = EngineManager()
    # time.sleep(10)
    em.add_camera()

    time.sleep(10)

    em.add_camera()
    print('Engine Manager Finished')
