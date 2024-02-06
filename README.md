# Celantur: Code Samples 

Here, you find code samples on using Celantur.

## Container API v1 Async Upload/Download

> [!NOTE]
> This functionality is available starting from `24.02.2` version of Container API

The examples are excessive but split on functions that could be easily copied and accommodated for your needs.

To run those scripts, make sure you switched to `server` folder:
```shell
cd server
```

Before using the examples, make sure you have installed dependencies from [requirements.txt](server/requirements.txt)
```shell
pip install -r requirements.txt
```

* [container-api-v1-upload-async-multiple-images.py](server/container-api-v1-upload-async-multiple-images.py)
  Example for uploading multiple images at once, and polling the status then downloading.
* [container-api-v1-upload-async-multiple-videos.py](server/container-api-v1-upload-async-multiple-videos.py)
  Example for uploading multiple videos at once, and polling the status then downloading.
  
