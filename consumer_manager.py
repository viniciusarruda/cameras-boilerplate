import multiprocessing as mp
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


class ConsumerManager(mp.Process):

    def __init__(self, consumer_list: list, input_queue, output_queue):
        super().__init__()

        self.fps = FPS()
        self.input_queue = input_queue
        self.output_queue = output_queue

        self.consumer_list = consumer_list
        self.consumers = []

    def init(self):

        for name, C, c_args in self.consumer_list:
            conn1, conn2 = mp.Pipe(duplex=True)  # can be optimized changing pipe to shared memory, but I'll need to manage some stuff
            cp = C(*c_args, conn2)
            cp.start()
            self.consumers.append((name, cp, conn1))

    def run(self):

        self.init()

        while True:

            self.fps.tick()

            frame_id, camera_id, frame = self.input_queue.get()

            for _, _, conn in self.consumers:
                conn.send((frame_id, camera_id, frame))  # pipe's send is blocking, i.e., no lock needed

            result = {}
            for name, _, conn in self.consumers:
                result[name] = conn.recv()  # pipe's recv is blocking, i.e., no lock needed

            self.output_queue.put_nowait((frame_id, camera_id, frame, result)) # acho que deveria ser uma queue pq a internet pode oscilar caso a api esteja fora do host da engine

            self.fps.tack()
            print('Full FPS: ', self.fps.fps)
