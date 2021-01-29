import multiprocessing as mp
import numpy as np
from multiprocessing.shared_memory import SharedMemory


class ConsumerManager(mp.Process):

    def __init__(self, consumer_list: list, camera_management_pipe, output_queue):
        super().__init__()

        self.camera_management_pipe = camera_management_pipe
        self.output_queue = output_queue
        self.camera_frames = {}

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

            if self.camera_management_pipe.poll():
                camera_id, name, condition, frame_id_name, cmd = self.camera_management_pipe.recv()
                frame = SharedMemory(name)
                frame_id = SharedMemory(frame_id_name)
                self.camera_frames[camera_id] = (condition, frame_id, frame)

            if len(self.camera_frames) > 0:

                for camera_id, (condition, frame_id_buf, frame_buf) in self.camera_frames.items():

                    with condition:

                        condition.wait()

                        frame_id = np.frombuffer(frame_id_buf.buf, dtype=np.uint64)
                        frame = np.frombuffer(frame_buf.buf, dtype=np.uint8).reshape((1080, 1920, 3))

                        for _, _, conn in self.consumers:
                            conn.send((0, 0, frame))  # pipe's send is blocking, i.e., no lock needed

                        result = {}
                        for name, _, conn in self.consumers:
                            result[name] = conn.recv()  # pipe's recv is blocking, i.e., no lock needed

                        self.output_queue.put_nowait((frame_id[0], camera_id, frame, result))

                        # lock_aux[0] = 0
