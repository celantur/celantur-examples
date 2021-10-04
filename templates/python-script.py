#!/usr/bin/env python3
import argparse
import logging
import sys


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Celantur: Template python script",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input", help="Required (integer) argument", type=int)  # argument to type is a type-casting function, default is `str`
    parser.add_argument("-a", "--arg1", help="Optional argument")
    parser.add_argument("-b", "--arg2", help="Required argument", required=True)
    parser.add_argument("-c", "--binary-flag", help="Binary flag", action="store_true", default=False)
    return parser


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s - %(processName)s/%(threadName)s - %(levelname)s - %(message)s",
                        level=logging.DEBUG)
    args = parser().parse_args()

    print("Should we display the arguments?")
    while True:
        prompt = input("Enter 'yes' or 'no': ")
        if prompt == "yes":
            logging.info(args)
            break
        elif prompt == 'no':
            sys.exit(0)

