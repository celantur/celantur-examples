## Overview 

There are two scripts in this folder that serve a purpose to anonymise images in the `.mcap` files. 

1. At first you need to extract images from `input.mcap` bag to `output_dir` with the `extract_images.py` script. 
2. Anonymise images from `output_dir` with [Celantur container](https://doc.celantur.com/container/getting-started) to some `anonimysed_dir`
3. Merge `input.mcap` file with `anonymised_dir` into the `mcap_output_dir`

### Dependencies
Follow [this guide](https://docs.ros.org/en/rolling/Installation/Ubuntu-Install-Debians.html) to install ros2 python packages for Ubuntu.
By default, after installation the dependencies are not in the python environment and to add them you need to run following code in the terminal you run your scripts from:
```
source /opt/ros/rolling/setup.bash
```


---
### Extract images from the `.mcap` file
Run 
```
python3 extract_images.py --input input.mcap --output output_dir
```
---
### Anonymisation
Follow [this guide](https://doc.celantur.com/container/usage/batch-and-stream-mode) to anonymise images using Celantur container in the batch mode.

---
### Merge anonymised images back into the `.mcap` file
Run 
```
python3 merge_anonymised_files.py --input input.mcap \
                                  --anonymised-images anonymised_dir \
                                  --output mcap_output_dir 
```
Optionally, if the output folder is not empty you can add `--overwrite` flag that will **COMPLETELY OVERWRITE** the `mcap_output_dir` in case it already exists.




