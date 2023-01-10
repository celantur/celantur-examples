import requests
import time

ENDPOINT_LOGIN = 'https://71pukv6wu8.execute-api.eu-central-1.amazonaws.com/prod/v1/signin'
ENDPOINT_FILE_GET = 'https://71pukv6wu8.execute-api.eu-central-1.amazonaws.com/prod/v1/file/'
ENDPOINT_FILE_STATUS = 'https://71pukv6wu8.execute-api.eu-central-1.amazonaws.com/prod/v1/file/'
IMAGE_FILE_NAME = 'G0041787.JPG'

#
# CELANTUR Cloud API Demo
#
def main():  
  
  auth_token = set_up()
  
  image = load_image()
  
  file_id = send_image(image, auth_token)

  receive_image(file_id, auth_token)


def set_up():
  f = open('user_info.txt') # provide your user credentials
  lines = f.readlines()
  data = {'username': lines[0].strip(), 'password': lines[1].strip()}
  f.close()
  response = requests.post(ENDPOINT_LOGIN, json=data, headers={'Content-Type':'application/json'})
  resp_dict = response.json()
  auth_token = resp_dict['AuthenticationResult']['AccessToken']
  print('Successfully authenticated and token received 🔒: ' + ENDPOINT_LOGIN)
  return auth_token

def load_image():
  image = ''
  try:
    image_file = open(IMAGE_FILE_NAME,'rb')
    image = image_file.read()
    image_file.close()
    print('Image loaded ✔️')
  except Exception as e:
    print(f'Could not read image: {e}')
  return image

def send_image(image, auth_token):
  file_id = ''
  image_upload_url = 'https://71pukv6wu8.execute-api.eu-central-1.amazonaws.com/prod/v1/file?method=blur&license_plate=True&face=True&name=example.jpg' # &debug=True&score=True
  try:
    print('Sending image to API ...')
    response = requests.post(image_upload_url, data=image, headers={'Authorization': auth_token})
    print('Image sent to API ✔️')
    response_body = response.json()
    print(response.json())
    file_id = response_body['file_id']
  except Exception as e:
    print(f'Could not send image. Cause: {e}')
  
  return file_id

def receive_image(file_id, auth_token):
  image_get_link = ENDPOINT_FILE_GET + file_id + '/anonymized' 
  image_status_link = ENDPOINT_FILE_STATUS + file_id + '/status'

  print('Querying image status from ' + image_status_link)
  seconds = 1.0
  counter = 1
  while (True):
    image_status_response_json = requests.get(image_status_link, headers={'Authorization': auth_token}).json()
    if image_status_response_json['file_status'] == "done":
      print(image_status_response_json)
      break
    message = "[{0}], Status: {1}, sleeping {2} sec ..."
    print(message.format(counter, image_status_response_json['file_status'], seconds))
    counter = counter + 1
    time.sleep(seconds)
  
  image_get_response = requests.get(image_get_link, headers={'Authorization': auth_token})
  
  with open('result.JPG', 'wb') as f:
    f.write(image_get_response.content)
    print('Anonymized image received 👍')
  

if __name__ == "__main__":
    main()
