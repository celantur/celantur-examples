#!/usr/bin/env python3
import socket
from datetime import datetime
import cv2
import numpy as np
from io import BytesIO

HOST, PORT = "localhost", 9999
INPUT = 'input/sample.jpg'
OUTPUT = "output/sample.jpg"

# Use the same buffer size as the server!
BUFSIZE = 4096

now = datetime.now


def send_image(connection: socket.socket, image: np.ndarray):
    with BytesIO() as fp:
        # Disable pickle for security, cf https://numpy.org/doc/stable/reference/generated/numpy.load.html
        np.save(fp, image, allow_pickle=False)
        fp.flush()
        content = fp.getvalue()
    filesize = len(content)
    content = filesize.to_bytes(BUFSIZE, "big") + content
    connection.sendall(content)
    print(f"{now().strftime('%H:%M:%S,%f')} - Sent {filesize} bytes.")


def receive_image(connection: socket.socket) -> np.ndarray:
    header = connection.recv(BUFSIZE)
    filesize = int.from_bytes(header, "big")
    content = bytearray()
    while len(content) < filesize:
        content += connection.recv(BUFSIZE)
    print(f"{now().strftime('%H:%M:%S,%f')} - Received {len(content)} bytes.")
    with BytesIO(content) as fp:
        array = np.load(fp, allow_pickle=False)
    return array


def process_image(image: np.ndarray, trial=0) -> np.ndarray:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            send_image(s, image)
            s.shutdown(socket.SHUT_WR)
            array = receive_image(s)
            return array
    except ValueError as e:
        if trial <= 5:
            print(e)
            return process_image(image, trial+1)
        else:
            raise e


if __name__ == "__main__":
    print(f"{now().strftime('%H:%M:%S,%f')} - Load image {INPUT}.")
    orig_image = cv2.imread(INPUT)
    for i in range(100):
        print(f"Iteration {i}:".upper())
        image = process_image(orig_image)

    print(f"{now().strftime('%H:%M:%S,%f')} - Save image to {OUTPUT}.")
    cv2.imwrite(OUTPUT, image)
    print(f"{now().strftime('%H:%M:%S,%f')} - DONE")

