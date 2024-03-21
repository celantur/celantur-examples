# Container Server modes

- Container REST API 
  - [synchronous mode](./celantur-api-client.py)
  - asynchronous mode, see section below.
- Container TCP modes
  - [JPEG I/O](./celantur-jpeg-client.py)
  - [NumPy array I/O](./celantur-numpy-client.py)

## Container API v1 Async Upload/Download

> [!NOTE]
> This functionality is available starting from `24.02.2` version of Container API

The examples are excessive but split on functions that could be easily copied and accommodated for your needs.

Before using the examples, make sure you have installed dependencies from [requirements.txt](server/requirements.txt)
```shell
pip install -r requirements.txt
```

* [container-api-v1-upload-async-multiple-images.py](server/container-api-v1-upload-async-multiple-images.py)
  Example for uploading multiple images at once, and polling the status then downloading.
* [container-api-v1-upload-async-multiple-videos.py](server/container-api-v1-upload-async-multiple-videos.py)
  Example for uploading multiple videos at once, and polling the status then downloading.
