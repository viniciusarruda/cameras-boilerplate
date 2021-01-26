import multiprocessing as mp
from camera import Camera
from consumer_manager import ConsumerManager
from consumers.consumerA import ConsumerExampleA
from consumers.consumerB import ConsumerExampleB


class EngineManager:

    def __init__(self):
        super().__init__()

        self.cameras = {}
        self.camera_id = 0

        self.input_queue = mp.Queue(maxsize=4)
        self.output_queue = mp.Queue(maxsize=100)

        self.cm = ConsumerManager([('nameA', ConsumerExampleA, ('paramA',)),
                                   ('nameB', ConsumerExampleB, ('paramB',))],
                                  self.input_queue,
                                  self.output_queue)
        self.cm.start()

    # receive through gRPC
    def add_camera(self, url):

        camera_id = self.camera_id  # get from db after inserting it
        data = {'id': camera_id, 'url': url}

        terminate = mp.Value('B', 0)
        crop_roi = mp.Value('B', 0)
        width = mp.Value('I', 0)
        height = mp.Value('I', 0)
        x = mp.Value('I', 0)
        y = mp.Value('I', 0)
        camera_p = Camera(data, {}, self.input_queue, False, terminate, crop_roi, width, height, x, y)  # colocar esses parametros em um dict
        # camera_p.daemon = True
        camera_p.start()

        self.cameras[camera_id] = (camera_p, terminate)
        self.camera_id += 1

    # gRPC function
    def receive_results(self):

        while True:
            ret = self.output_queue.get()
            # do something with ret like sending it to an API


if __name__ == "__main__":
    em = EngineManager()

    url = 'rtsp://your_url_here'
    em.add_camera(url)

    em.receive_results()

    print('Engine Manager Finished')
