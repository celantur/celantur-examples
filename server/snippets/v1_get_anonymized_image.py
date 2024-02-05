import logging

import requests


def v1_get_anonymized_image(host, port, uid, scheme="http"):
    """
    Getting anonymized image
    """
    url = f"{scheme}://{host}:{port}"
    endpoint = f"v1/file/{uid}/anonymised"

    resp = requests.get(
        f"{url}/{endpoint}",
    )

    logging.debug("Received response (%s) for \"%s\"", resp.status_code, f"/{endpoint}")
    if 200 <= resp.status_code < 400:
        return resp.content

    raise Exception(f"Issues with download happen. Content: {resp.content}")
