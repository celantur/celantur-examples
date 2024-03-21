import logging
from os.path import basename
from time import sleep

import requests


def v1_upload_async(host, port, file_path, params, file_mime, scheme="http"):
    """
    Asynchronously upload file

    Can be used for both images and videos
    """
    url = f"{scheme}://{host}:{port}"
    endpoint = "v1/file"

    file_name = basename(file_path)
    with open(file_path, "rb") as fd:
        file_blob = fd.read()

    upload = {
        "fileobject": (file_name, file_blob, file_mime)
    }

    resp = requests.post(
        f"{url}/{endpoint}",
        params=params,
        files=upload,
        headers={"x-is-async": "1"}
    )

    logging.debug("Received response (%s) for \"%s\"", resp.status_code, f"/{endpoint}")
    if 200 <= resp.status_code < 400:
        return resp.json()["id"]

    raise Exception(f"Issues with upload happen. Content: {resp.content}")
