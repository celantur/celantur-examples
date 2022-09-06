#!/usr/bin/env python3
import socket
from datetime import datetime
import cv2
import numpy as np
from io import BytesIO
import argparse
import os

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--input", help="Input directory.", required=True)
parser.add_argument("-o", "--output", help="Output directory.", required=True)
parser.add_argument("--host", help="Host address", default="localhost")
parser.add_argument("--port", help="Port number", type=int, default=9999)
parser.add_argument("--buffer-size", help="Buffer size in bytes. Use the same buffer size as the server!",
                    type=int, default=4096)
args = parser.parse_args()

now = datetime.now


def send_image(connection: socket.socket, image: np.ndarray):
    with BytesIO() as fp:
        # Disable pickle for security, cf https://numpy.org/doc/stable/reference/generated/numpy.load.html
        np.save(fp, image, allow_pickle=False)
        fp.flush()
        content = fp.getvalue()
    filesize = len(content)
    content = filesize.to_bytes(args.buffer_size, "big") + content
    connection.sendall(content)
    print(f"{now().strftime('%H:%M:%S,%f')} - Sent {filesize} bytes.")


def receive_image(connection: socket.socket) -> np.ndarray:
    header = connection.recv(args.buffer_size)
    filesize = int.from_bytes(header, "big")
    content = bytearray()
    while len(content) < filesize:
        content += connection.recv(args.buffer_size)
    if len(content) == 0:
        raise ValueError("Received 0 bytes from Celantur Container!")
    else:
        print(f"{now().strftime('%H:%M:%S,%f')} - Received {len(content)} bytes.")
    with BytesIO(content) as fp:
        array = np.load(fp, allow_pickle=False)
    return array


def process_image(image: np.ndarray, trial=0) -> np.ndarray:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((args.host, args.port))
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

    for filename in os.listdir(args.input):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            INPUT = os.path.join(args.input, filename)
            OUTPUT = os.path.join(args.output, filename)
            print(f"{now().strftime('%H:%M:%S,%f')} - Load image {INPUT}.")
            orig_image = cv2.imread(os.path.join(args.input, filename))
            # print(f"Iteration {filename}:".upper())
            image = process_image(orig_image)
            print(f"{now().strftime('%H:%M:%S,%f')} - Save image to {OUTPUT}.")
            cv2.imwrite(OUTPUT, image)
            print(f"{now().strftime('%H:%M:%S,%f')} - DONE")

