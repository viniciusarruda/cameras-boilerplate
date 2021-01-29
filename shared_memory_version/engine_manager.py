import multiprocessing as mp
from camera import Camera
from consumer_manager import ConsumerManager
from consumers.consumerA import ConsumerExampleA
from consumers.consumerB import ConsumerExampleB
import numpy as np
from multiprocessing.managers import SharedMemoryManager
import cv2
import time


# ~30 FPS
class FPS:

    def __init__(self):

        self.start_time = None
        self.fps = 0

    def tick(self):
        self.start_time = time.time()

    def tack(self):
        tmp_fps = 1.0 / (time.time() - self.start_time)
        self.fps = 0.9 * self.fps + 0.1 * tmp_fps


class EngineManager:

    def __init__(self, smm):
        super().__init__()

        self.fps = FPS()
        self.cameras = {}
        self.smm = smm

        self.manager = mp.Manager()
        conn, self.camera_management_pipe = mp.Pipe()
        self.output_queue = mp.Queue(maxsize=100)

        self.cm = ConsumerManager([('nameA', ConsumerExampleA, ('paramA',)),
                                   ('nameB', ConsumerExampleB, ('paramB',))],
                                  conn,
                                  self.output_queue)
        self.cm.start()

        self.frame_info = {}

    # receive through gRPC
    def add_camera(self, camera_id, url):

        data = {'id': camera_id, 'url': url}

        terminate = mp.Value('B', 0)
        crop_roi = mp.Value('B', 0)

        w = mp.Value('I', 0)
        h = mp.Value('I', 0)
        x = mp.Value('I', 0)
        y = mp.Value('I', 0)

        np_array = np.zeros((1080, 1920, 3), dtype=np.uint8)
        shm = self.smm.SharedMemory(np_array.nbytes)

        condition = self.manager.Condition()

        np_array = np.zeros(1, dtype=np.uint64)
        shm_frame_id = self.smm.SharedMemory(np_array.nbytes)

        camera_p = Camera(data, shm.name, condition, shm_frame_id.name, False, terminate, crop_roi, w, h, x, y)
        camera_p.start()

        self.camera_management_pipe.send((camera_id, shm.name, condition, shm_frame_id.name, 'add'))

        self.cameras[camera_id] = (camera_p, terminate)

    # gRPC function
    def receive_results(self):

        while True:
            self.fps.tick()
            frame_id, camera_id, frame, result = self.output_queue.get()
            self.fps.tack()
            self.frame_info['count'][camera_id] += 1
            self.frame_info['last'][camera_id] = frame_id
            print('Full FPS: ', self.fps.fps, self.frame_info)
            frame = cv2.resize(frame, (1920 // 2, 1080 // 2))

            cv2.putText(frame, f'Camera ID {camera_id}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0,255), 2)
            cv2.putText(frame, f'Frame ID {frame_id}', (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0,255), 2)

            for i, (k, v) in enumerate(result.items()):
                cv2.putText(frame, f'Result of {k}: {v}', (10, 90 + (i * 30)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0,255), 2)

            cv2.imshow('frame', frame)
            # do something with ret like sending it to an API
            if cv2.waitKey(1) & 0xFF == ord('q'): # wait for 1 millisecond
                break

        cv2.destroyAllWindows()


if __name__ == "__main__":

    with SharedMemoryManager() as smm:
        em = EngineManager(smm)

        url = 'rtsp://Admin:1234@10.5.1.10:554/rtsp/profile1'
        em.add_camera(10, url)

        url = 'rtsp://Admin:1234@192.168.5.100:554/rtsp/profile1'
        em.add_camera(20, url)

        url = 'rtsp://Admin:1234@192.168.5.101:554/rtsp/profile1'
        em.add_camera(30, url)

        em.frame_info = {'count': {10: 0, 20: 0, 30: 0}, 'last': {10: 0, 20: 0, 30: 0}}

        em.receive_results()

    print('Engine Manager Finished')
