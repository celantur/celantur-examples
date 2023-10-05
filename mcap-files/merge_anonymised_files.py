#!/usr/bin/python3
import argparse
import os
import shutil

import cv2
from yaml import serialize
import rosbag2_py
from rclpy.serialization import serialize_message, deserialize_message
from rosidl_runtime_py.utilities import get_message
from std_msgs.msg import String

if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--input", help="Input bag path (.mcap file) to read from.", required=True
    )
    parser.add_argument(
        "--anonimized-images", help="Input folder to read anonymized images from.", required=True
    )
    parser.add_argument("--output", help="Output folder to write to.",required=True)
    parser.add_argument("--overwrite", help="Overwrite output folder if it exists.", action="store_true")
    args = parser.parse_args()

    if os.path.exists(args.output):
        if not args.overwrite:
            raise ValueError(f"Output folder {args.output} already exists. Use --overwrite to overwrite.")
        if args.overwrite:
            shutil.rmtree(args.output)
    

    writer = rosbag2_py.SequentialWriter()
    writer.open(
        rosbag2_py.StorageOptions(uri=args.output, storage_id="mcap"),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr", output_serialization_format="cdr"
        ),
    )

    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=args.input, storage_id="mcap"),
        rosbag2_py.ConverterOptions(
            input_serialization_format="cdr", output_serialization_format="cdr"
        ),
    )

    topic_types = reader.get_all_topics_and_types()
    for t in topic_types:
        writer.create_topic(t)
    
    def typename(topic_name):
        for topic_type in topic_types:
            if topic_type.name == topic_name:
                return topic_type.type
        raise ValueError(f"topic {topic_name} not in bag")
    
    while reader.has_next():
        topic, data, timestamp = reader.read_next()
        msg_type = get_message(typename(topic))
        msg = deserialize_message(data, msg_type)
        if topic.split('/')[-1] == 'image_raw':
            frame_id = msg.header.frame_id
            ts = msg.header.stamp.nanosec
            img_name=f'{frame_id}_{ts}.png'
            image = cv2.imread(os.path.join(args.anonimized_images, img_name))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            msg.data = image.tobytes()
            data = serialize_message(msg)
            # h,w = msg.height, msg.width
            # arr = np.array(msg.data.tolist()).reshape((h,w,3))
            # cv2.imwrite(os.path.join(args.output, img_name), arr)
        writer.write(topic, data, timestamp)
