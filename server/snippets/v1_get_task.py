import logging

import requests


def v1_get_task(host, port, uid, scheme="http"):
    """
    Getting information about uploaded file
    """
    url = f"{scheme}://{host}:{port}"
    endpoint = f"v1/task/{uid}"

    resp = requests.get(f"{url}/{endpoint}")

    logging.debug("Received response (%s) for \"%s\"", resp.status_code, f"/{endpoint}")
    if 200 <= resp.status_code < 400:
        return resp.json()

    logging.error("Issues with getting task happen. Content: %s", resp.content)
    return None
