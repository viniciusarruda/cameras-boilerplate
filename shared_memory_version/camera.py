import cv2
from multiprocessing import Process
import numpy as np
from multiprocessing.shared_memory import SharedMemory


class Camera(Process):

    def __init__(self, data: dict, name, condition, frame_id_name, already_exists: bool, terminate, crop_roi, width, height, x, y):
        super().__init__()

        self.shm = SharedMemory(name)
        self.frame = np.frombuffer(self.shm.buf, dtype=np.uint8).reshape((1080, 1920, 3))

        self.shm_frame_id = SharedMemory(frame_id_name)
        self.frame_id_shm = np.frombuffer(self.shm_frame_id.buf, dtype=np.uint64)

        self.condition = condition

        self.already_exists = already_exists

        self.id = data['id'] if 'id' in data else None
        self.url = data['url']  # Not optional
        self.resolution = data['resolution'] if 'resolution' in data else None
        self.roi = data['roi'] if 'roi' in data else None

        self.frame_id = None
        self.cap_fps = None
        self.cap_bitrate = None

        self.terminate = terminate
        self.crop_roi = crop_roi
        self.crop_roi_was_set = self.crop_roi.value
        self.width = width
        self.height = height
        self.x = x
        self.y = y

    def connect(self):

        print('Connecting...')
        self.cap = cv2.VideoCapture(self.url)
        height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)

        if not self.already_exists:

            self.width.value = int(width)
            self.height.value = int(height)
            self.x.value = 0
            self.y.value = 0
            self.resolution = {'w': int(width), 'h': int(height)}
            self.roi = {'x': 0, 'y': 0, 'w': self.resolution['w'], 'h': self.resolution['h']}
        else:
            assert self.resolution['w'] == int(width) and self.resolution['h'] == int(height), f"Resolution retrieved is different of the camera capture! {self.resolution['w']} == {int(width)} and {self.resolution['h']} == {int(height)}"

        self.cap_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.cap_bitrate = self.cap.get(cv2.CAP_PROP_BITRATE)

        print('Connected!')

    def preprocessing(self, frame):

        # Do your preprocessing here!
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # crop to roi
        if self.crop_roi.value:

            if not self.crop_roi_was_set:  # ligou agora
                self.roi = {'x': self.x.value, 'y': self.y.value, 'w': self.width.value, 'h': self.height.value}
                self.crop_roi_was_set = True

            frame = frame[self.roi['y']:self.roi['y'] + self.roi['h'],
                          self.roi['x']:self.roi['x'] + self.roi['w']]

        elif self.crop_roi_was_set:  # desligou agora
            self.roi = {'x': 0, 'y': 0, 'w': self.resolution['w'], 'h': self.resolution['h']}
            self.crop_roi_was_set = False

        return frame

    def run(self):

        self.connect()

        assert self.cap.isOpened()

        self.frame_id = 0

        while not self.terminate.value:
            self.cap.grab()

            if self.condition.acquire(blocking=False):
                _, frame = self.cap.retrieve()
                frame = self.preprocessing(frame)
                np.copyto(self.frame, frame)
                self.frame_id_shm[0] = self.frame_id
                self.condition.notify()
                self.condition.release()

            self.frame_id += 1

        self.cap.release()
