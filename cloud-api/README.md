# Cloud API clients

## Cloud API v2

1. If you have not yet done so: Set up username and password in [Celantur App](https://app.celantur.com)
2. Create a new folder, e..g 'Celantur', 
   with an input folder, e.g. 'input', 
   and an output folder, e.g. 'output'.
3. Download [script](./cloud-api-v2-client.py) and 
   [example configuration](./example-config.json) into the folder.
4. Install dependencies with `pip install -r requirements.txt`
5. Run script: <br /> 
   `python3 cloud-api-v2-client.py -u $USERNAME -p $PASSWORD -i input/ -o output/ -c example-config.json` <br />
   (you need to replace `$USERNAME` and `$PASSWORD` with your actual passwords.)
