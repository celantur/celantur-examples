import logging

import requests


def v1_get_anonymized_video(host, port, uid, scheme="http"):
    """
    Getting anonymized video
    """
    url = f"{scheme}://{host}:{port}"
    endpoint = f"v1/file/{uid}/video/anonymised"

    resp = requests.get(
        f"{url}/{endpoint}",
    )

    logging.info("Received response (%s) for \"%s\"", resp.status_code, f"/{endpoint}")
    if 200 <= resp.status_code < 400:
        return resp.content

    raise Exception(f"Issues with download happen. Content: {resp.content}")
