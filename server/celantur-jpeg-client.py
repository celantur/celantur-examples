#!/usr/bin/env python3
import os
import socket
from datetime import datetime
import PIL.Image

HOST, PORT = "localhost", 9999
INPUT = 'input/sample.jpg'
OUTPUT = "output/sample.jpg"

now = datetime.now
size = os.path.getsize(INPUT)
print(f"File size of {INPUT}: {size} bytes")

for i in range(5):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        with open(INPUT, "rb") as fp:
            r = s.sendfile(fp)
            print(f"{now().strftime('%H:%M:%S,%f')} - Sent {r} bytes to server.")
        s.shutdown(socket.SHUT_WR)
        output_buffer = s.makefile('rb')
        image = PIL.Image.open(output_buffer)
        print(f"{now().strftime('%H:%M:%S,%f')} - Save image to {OUTPUT}.")
        image.save(OUTPUT)

print("DONE")
