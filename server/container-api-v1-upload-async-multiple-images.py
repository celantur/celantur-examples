#!/bin/env python3
import logging
import os
from logging import getLevelName
from os import makedirs
from os.path import join, basename
from sys import argv
from time import sleep

from snippets.v1_get_anonymized_image import v1_get_anonymized_image
from snippets.v1_get_task import v1_get_task
from snippets.v1_upload_async import v1_upload_async


def log_details(host: str, port: int, folder: str, files: list, level: str):
    """
    Printing out app information before starting
    """
    logging.basicConfig(level=level)
    logging.info("## Async Upload/Download Images")
    logging.info("## Celantur API Host: %s", host)
    logging.info("## Celantur API Port: %s", port)
    logging.info("## File(s) for upload: %s", ", ".join(files))
    logging.info("## Download folder: %s", folder)


def upload_async_files(host: str, port: int, files: list, params: dict, mime_type):
    """
    Async upload files
    """
    requested_task_files = {}

    # First uploading all the files with a single loop
    logging.info(">> Uploading files")
    for file_path in files:

        # Performing async upload, and obtaining task uid
        uid = v1_upload_async(host, port, file_path, params, mime_type)

        if not uid:
            raise Exception("Task couldn't have been found")
        requested_task_files[uid] = file_path

    return requested_task_files


def download_async_anonymized_files(host: str, port: int, folder: str, requested_task_files: dict, polling_retry_sec: int):
    """
    Async download anonymized files
    """
    processed_task_uids = []
    failed_task_uids = []

    # Second checking the status and download processed ones
    logging.info("Downloading anonymized files...")
    while len(processed_task_uids + failed_task_uids) != len(requested_task_files):
        for uid, file_path in requested_task_files.items():
            # Getting task to check the status
            if task := v1_get_task(host, port, uid):
                if task["status"] == "done":
                    processed_task_uids.append(uid)

                    anonymized_file_blob = v1_get_anonymized_image(host, port, uid)
                    anonymized_file_path = join(folder, basename(file_path))

                    with open(anonymized_file_path, "wb") as fd:
                        fd.write(anonymized_file_blob)

                    logging.info("<< Anonymized file downloaded to %s", anonymized_file_path)

                elif task["status"] in ("failed", "deleted"):
                    failed_task_uids.append(uid)
                    logging.error("Task %s failed", uid)

        logging.debug("Polling anonymized image. Retry in %s seconds", polling_retry_sec)

        sleep(polling_retry_sec)


def main(files: list, params: dict, mime_type):
    if len(files) == 0:
        raise Exception("Please specify at least one file")

    folder = os.environ.get("CELANTUR_DOWNLOAD_DIR") or join("/tmp", "celantur")
    host = os.environ.get("CELANTUR_HOST") or "127.0.0.1"
    port = os.environ.get("CELANTUR_PORT") or 7000
    polling_retry_sec = os.environ.get("CELANTUR_POLLING_RETRY") or 3
    debug_level = getLevelName(os.environ.get("CELANTUR_DEBUG_LEVEL") or "INFO")

    makedirs(folder, exist_ok=True)

    # Logging details about run
    log_details(host, port, folder, files, debug_level)

    # Uploading files asynchronously
    requested_task_files = upload_async_files(host, port, files, params, mime_type)

    # Downloading files asynchronously through polling
    download_async_anonymized_files(host, port, folder, requested_task_files, polling_retry_sec)


if __name__ == "__main__":
    params = {
        "face": True,
        "method": "blur"
    }
    mime_type = "image/jpg"
    main(argv[1:], params, mime_type)
