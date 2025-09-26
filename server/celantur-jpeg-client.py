#!/usr/bin/env python3
import os
import socket
from datetime import datetime
import PIL.Image
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--input", help="Input directory.", required=True)
parser.add_argument("-o", "--output", help="Output directory.", required=True)
parser.add_argument("--host", help="Host address", default="localhost")
parser.add_argument("--port", help="Port number", type=int, default=9999)
args = parser.parse_args()

for filename in os.listdir(args.input):
    if os.path.splitext(filename)[1].lower() in [".jpeg", ".jpg"]:
        file = os.path.join(args.input, filename)
        now = datetime.now
        size = os.path.getsize(file)
        print(f"File size of {file}: {size} bytes")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((args.host, args.port))
            with open(file, "rb") as fp:
                r = s.sendfile(fp)
                print(f"{now().strftime('%H:%M:%S,%f')} - Sent {r} bytes to server.")
            s.shutdown(socket.SHUT_WR)
            output_buffer = s.makefile('rb')
            output_file = os.path.join(args.output, filename)
            print(f"{now().strftime('%H:%M:%S,%f')} - Save image to {output_file}.")
            with open(output_file, "wb") as f:
                f.write(output_buffer.read())

print("DONE")
