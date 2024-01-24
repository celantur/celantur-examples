#!/usr/bin/python3

"""
Script that reads ROS2 messages from an MCAP bag using the rosbag2_py API.

SETUP:
Follow this guide: https://docs.ros.org/en/rolling/Installation/Ubuntu-Install-Debians.html 

sudo add-apt-repository universe

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update && sudo apt upgrade
sudo apt install ros-rolling-ros-base

BEFORE RUNNING SCRIPT
source /opt/ros/rolling/setup.bash #to export PYTHONPATH and libraries. 
"""

import argparse
import os

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import numpy as np
import cv2


def read_messages(input_bag: str):
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=input_bag, storage_id="mcap"),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr", output_serialization_format="cdr"
        ),
    )

    topic_types = reader.get_all_topics_and_types()

    def typename(topic_name):
        for topic_type in topic_types:
            if topic_type.name == topic_name:
                return topic_type.type
        raise ValueError(f"topic {topic_name} not in bag")

    while reader.has_next():
        topic, data, timestamp = reader.read_next()
        msg_type = get_message(typename(topic))
        msg = deserialize_message(data, msg_type)
        yield topic, msg, timestamp
    del reader


def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--input", help="Input bag path (.mcap file) to read from.", required=True
    )
    parser.add_argument(
        "--output", help="Output folder to write images to.", default='extracted_images'
    )
    args = parser.parse_args()
    if (not os.path.exists(args.output)):
        os.makedirs(args.output)
    for topic, msg, timestamp in read_messages(args.input):
        if topic.split('/')[-1] == 'image_raw':
            frame_id = msg.header.frame_id
            ts = msg.header.stamp.nanosec
            img_name=f'{frame_id}_{ts}.png'
            h,w = msg.height, msg.width
            arr = np.array(msg.data.tolist()).reshape((h,w,3))
            if arr.dtype != np.uint8:
                img = arr.astype(np.uint8)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            cv2.imwrite(os.path.join(args.output, img_name), img)

if __name__ == "__main__":
    main()
