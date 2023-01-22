import requests

BASE = 'http://127.0.0.1:5000/'

try:
    response = requests.post(BASE + 'api_login', json={'email': 'worker1@gmail.com', 'password': 'keneda'})
    response.raise_for_status()
    data = response.json()
    user_id = data['user_id']
    if response.status_code == 200:
        # request was successful

        print(response.json())
    else:
        # request failed
        print(response.status_code)
except requests.exceptions.HTTPError as errh:
    print ("Http Error:",errh)
except requests.exceptions.ConnectionError as errc:
    print ("Error Connecting:",errc)
except requests.exceptions.Timeout as errt:
    print ("Timeout Error:",errt)
except requests.exceptions.RequestException as err:
    print ("Something went wrong:",err)



