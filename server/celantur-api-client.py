import json
from typing import List

import requests


class ImageQueryParams:
    def __init__(self, method: str = '', debug: bool = False,
                 score: bool = False,
                 save_mask: str = "",
                 watermark: bool = False,
                 face: bool = False,
                 license_plate: bool = False,
                 person: bool = False,
                 vehicle: bool = False,
                 bbox: bool = False,
                 format: str = "whole",
                 quality: int = 0,
                 ignores: str = ''):
        self.debug = debug
        self.score = score
        self.save_mask = save_mask
        self.watermark = watermark
        self.method = method
        self.face = face
        self.license_plate = license_plate
        self.person = person
        self.vehicle = vehicle
        self.format = format
        self.bbox = bbox
        self.quality = quality
        if ignores:
            self.ignores: List[dict] = json.loads(ignores)
        else:
            self.ignores = []

    def to_request(self):
        request = ""
        for key, value in self.__dict__.items():
            if request == "":
                request += "?" + str(key) + "=" + str(value)
            else:
                request += "&" + str(key) + "=" + str(value)
        return request

    def init_object_from_dict(self, params_dict):
        test_params = self.__init__()
        for key, value in params_dict.items():
            self.__dict__[key] = value
        return test_params


if __name__ == "__main__":
    base_url = "http://127.0.0.1:7000/v1"
    file_url = "/file"
    IMAGE_PATH = ''  # TODO enter image path
    params = {"face": "True", "method": "blur"}  # TODO add your parameters
    files = {"fileobject": ("test.jpg", open(IMAGE_PATH, "rb"), "image/jpg", {"Expires": "0"})}
    query_params = ImageQueryParams()
    query_params.init_object_from_dict(params_dict=params)
    response = requests.post(base_url + file_url + query_params.to_request(), files=files)
