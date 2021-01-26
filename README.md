# Cameras Consumer-Producer Boilerplate

A boilerplate of consumer-producer where the producer is a camera capture.

## Table of Contents

- [How it works](#how-it-works)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)

## How it works

The `engine_manager.py` makes the interface with the external world. In this file you should implement functions to be accessed externally via gRPC, HTTP request, function calls, or whatever you want.
Also, in this file you'll need to specify a list of consumers you want to have, just open the file and follow the example.
A function to add a new camera is already implemented, and you can follow the example to add more features.

The `consumer_manager.py` will be instantiated by the `EngineManager`, and its job is to handle the data received from the producers, sending to all consumers. Every consumer will receive the same data item, and after processing it, each result of each consumer will be placed together in a queue, which can be accessed via `EngineManager`.

The consumers must be implemented following the examples, and must inherit `multiprocessing.Process` and implement the `run()` function.

Lastly, `camera.py` capture the camera frames and put in a queue if is not full.

Every class in this code when instantiated will spawn a new process. Here the `multiprocessing` library is used to achieve real parallelism, escaping the python GIL, and `OpenCV` to capture the camera frames.

## Installation

Install `opencv-python` and clone this repo.

## Usage

Edit the URL at `engine_manager.py` file and `python engine_manager.py`.

## Contributing

This code is intended to be efficient. 
If you have tips or any comment that can benefit this code, please, do not hesitate to open an issue or a pull request.