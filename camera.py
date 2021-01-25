import cv2
import queue  # because multiprocessing borrowed queue's Queue
from multiprocessing import Process


class Camera(Process):

    def __init__(self, data: dict, callbacks: dict, queue, already_exists: bool, terminate, crop_roi, width, height, x, y):
        super().__init__()

        self.queue = queue
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

    def _check_parameters(self, data: dict, callbacks: dict):

        assert 'url' in data

        assert 'after_connect' in callbacks
        assert 'pre_processing' in callbacks

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

        self.connect()  # must be inside run not __init__

        assert self.cap.isOpened()

        self.frame_id = 0

        while not self.terminate.value:

            self.cap.grab()

            if not self.queue.full():

                _, frame = self.cap.retrieve()
                frame = self.preprocessing(frame)

                # While retrieving and preprocessing, the queue may be full, so this try/except
                try:
                    self.queue.put_nowait((self.frame_id, self.id, frame))
                except queue.Full:
                    print('Skiping.. queue is full!')

            self.frame_id += 1

        self.cap.release()
