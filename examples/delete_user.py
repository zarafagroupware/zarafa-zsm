import json

import requests
from requests.auth import HTTPBasicAuth

api_host = 'http://localhost:80'
user_uri = '/api/v1/tenants/c2387b2bcbb24e849cda5bb8e51f78c3/users/128ee207453b4d4cbc9f5afac1f0f012/'
url = api_host + user_uri

headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
}

response = requests.delete(url=url, headers=headers,
                         auth=HTTPBasicAuth('admin@origin', 'a'))
print response

