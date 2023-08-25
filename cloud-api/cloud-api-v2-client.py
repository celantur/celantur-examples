#!/usr/bin/python3

import requests
import time
import json
import threading
import logging 
import os 
import queue
import argparse


NUM_THREADS = 30  # Number of threads
TASKS_PER_AUTHENTICATION = 50 # Number of tasks before re-authentication

SLEEP_TIME = 10.0 # seconds wait time between querying request
MAX_CHECK_STATUS = 1000 # Retry 1000 times to check status before stopping
USERNAME: str
PASSWORD: str

def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
            description="Celantur Cloud API v2 Client",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input", help="Input folder containing images", required=True)
    parser.add_argument("-o", "--output", help="Output folder for saving anonymized images", required=True)
    parser.add_argument("-u", "--username", help="Username for Celantur Cloud API", required=True)
    parser.add_argument("-p", "--password", help="Password for Celantur Cloud API", required=True)
    parser.add_argument("-c", "--configuration", help="Anonymisation configuration as JSON file", required=True)
    parser.add_argument("-e", "--endpoint", help="Celantur Cloud API v2 endpoint", default='https://api.celantur.com/v2/')
    return parser



def setup_logger(log_dir='logs'):
    # Create the log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Get the current timestamp
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')

    # Define the log file name with timestamp
    log_file = f'{log_dir}/celantur-api-v2-client_{timestamp}.log'

    # Create the logger and set its level to DEBUG
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.DEBUG)

    # Create the file handler
    file_handler = logging.FileHandler(log_file)

    # Create the console handler
    console_handler = logging.StreamHandler()

    # Define the log format
    log_format = '[%(asctime)s] [%(threadName)s] [%(levelname)s]: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(log_format, date_format)

    # Set the formatter for both handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()


def get_files_from_(root_path: str, relative_path: str = "") -> str:
    path = os.path.join(root_path, relative_path)
    extensions = ['.jpg', '.jpeg', '.png']
    for file in os.scandir(path):
        if os.path.isfile(file) and os.path.splitext(file)[1].lower() in extensions:
            yield os.path.join(relative_path, file.name)
        elif os.path.isdir(file):
            yield from get_files_from_(root_path, os.path.join(relative_path, file.name))


def get_files_without_overwrite_from_(root_input_path: str, root_output_path: str, input_queue: queue.Queue):
    """
    Put input file paths into the queue
    """
    for file_path in get_files_from_(root_input_path):
        output_path = os.path.join(root_output_path, file_path)
        if os.path.exists(output_path):
            logger.info(f"Skip {file_path} because {output_path} already exists.")
        else:
           input_queue.put((root_input_path, file_path))
           logger.debug(f"Put into file queue: {file_path}")
           


def authenticate():
  data = {'username': USERNAME, 'password': PASSWORD}
  response = requests.post(ENDPOINT_LOGIN, json=data, headers={'Content-Type':'application/json'})
  resp_dict = response.json()
  try:
    auth_token = resp_dict['AccessToken']
    # TODO implement logic for token renewal before expiration
    # expires_in = resp_dict['ExpiresIn']  # 3600s
    logger.info('🔒 Successfully authenticated and token received.')
    return auth_token
  except:
     logger.error(f'Login error (Status {response.status_code}): {response.text}')
     raise SystemExit(-1)
     


def load_image(file_path: str):
  image = ''
  try:
    image_file = open(file_path,'rb')
    image = image_file.read()
    image_file.close()
    logger.debug(f'🖼️ Image loaded: {file_path}.')
  except Exception as e:
    logger.info(f'Could not read image: {e}')
  return image


def create_task(anonymisation_configuration: str, auth_token: str):
  response = requests.post(ENDPOINT_TASK, data=json.dumps(anonymisation_configuration), headers={'Authorization': auth_token})

  if response.status_code == 200:
    response_body = response.json()
    
    task_id = response_body['task_id']
    upload_url = response_body['upload_url']

    logger.info(f"Task {task_id} created.")
    return (task_id, upload_url)
  else:
    logger.error(f'Creating task failed (Status {response.status_code}): {response.text}')


def get_task_status(task_id: str, auth_token: str):
  # stati: new, queued, processing, done or failed
  status_url = f'{ENDPOINT_TASK}{task_id}/status'

  response = requests.get(status_url, headers={'Authorization': auth_token})  
  if response.status_code == 200:
    response_body = response.json()
    status = response_body['task_status']
    logger.info(f'Task {task_id} has status: {status}')
    return status
  else:
    logger.error(f'Getting task status failed (Status {response.status_code}): {response.text}')
    return response.status_code
  

def get_task(task_id: str, auth_token: str):
  # stati: new, queued, processing, done or failed
  task_url = f'{ENDPOINT_TASK}{task_id}'

  response = requests.get(task_url, headers={'Authorization': auth_token})  
  response_body = response.json()
  if response.status_code == 200:
    logger.info(f'GET /task/{task_id} successful.')
    return response_body
  else:
    logger.error(f'Getting task faild (Status {response.status_code}): {response.text}')
    return 0


def upload_image(file_path: str, upload_url: str):
  img = load_image(file_path)
  response = requests.put(url=upload_url, data=img)
  if response.status_code == 200:
    logger.info(f'⬆️ Uploaded image {file_path} successfully.')
    return True
  else:
    logger.error(f'Image upload failed (Status {response.status_code}): {response.text}')
    return False


def download_image(output_file_name: str, task_id: str, auth_token: str, sleep_time: float):
  global total_count
  counter = 1
  while counter < MAX_CHECK_STATUS:
    task_status = get_task_status(task_id, auth_token)
    if task_status == "done":
      break
    logger.info(f"[Retry {counter}/{MAX_CHECK_STATUS}] Status: {task_status}, sleeping {sleep_time} seconds ...")
    counter += 1
    time.sleep(sleep_time)
  else:
     if task_status != 'done':
        logger.warning(f"The task {task_id} did not finish.")
  
  task = get_task(task_id, auth_token)

  anonymized_url = task['anonymized_url']
  response = requests.get(anonymized_url)
  os.makedirs(os.path.dirname(output_file_name), exist_ok=True)  
  with open(output_file_name, 'wb') as f:
    f.write(response.content)
  logger.info(f'[image {total_count}] Anonymized image {output_file_name} received 👍.')
  logger.info(f'Task {task_id} completed.')

def run_test(input_queue: queue.Queue, output_folder: str, anonymisation_configuration: dict):
  global auth_token, total_count
  while not input_queue.empty():
    input_root_path, relative_file_path = input_queue.get()
    task_id, upload_url = create_task(anonymisation_configuration, auth_token)
    input_file_path = os.path.join(input_root_path, relative_file_path)
    output_file_path = os.path.join(output_folder, relative_file_path)
    if upload_image(input_file_path, upload_url):
      download_image(output_file_path, task_id, auth_token, SLEEP_TIME)
    total_count += 1
    if total_count % TASKS_PER_AUTHENTICATION == 0:  # Re-authenticate
        auth_token = authenticate()


def read_configuration_file(file_name: str) -> dict:
   if file_name is None:
      raise ValueError("No configuration specified!")
   else:
    with open(file_name, 'r') as fp:
       return json.load(fp)


def create_thread(*run_test_args) -> threading.Thread:
  thread = threading.Thread(target=run_test, args=run_test_args)
  thread.start()
  return thread


if __name__ == "__main__":
    total_count = 0
    # Measure the execution time
    start_time = time.time()
    args = parser().parse_args()
    endpoint: str = args.endpoint.rstrip('/')
    configuration: dict = read_configuration_file(args.configuration)

    ENDPOINT_LOGIN = f'{endpoint}/signin/'
    ENDPOINT_TASK = f'{endpoint}/task/'
    USERNAME = args.username
    PASSWORD = args.password
    

    logger.info(f"Start Cloud API v2 Client with {NUM_THREADS} threads.")

    input_queue = queue.Queue(maxsize=100)
    file_reader = threading.Thread(name="ReadInput", target=get_files_without_overwrite_from_, args=(args.input, args.output, input_queue))
    file_reader.start()

    auth_token = authenticate()

    threads = [create_thread(input_queue, args.output, configuration) for _ in range(NUM_THREADS)]
    for t in threads:
        t.join()
    file_reader.join()
    end_time = time.time()

    # Calculate the elapsed time
    elapsed_time = end_time - start_time
    logger.info(f"Completed. It took {int(elapsed_time)} seconds ({elapsed_time//60} minutes)")

