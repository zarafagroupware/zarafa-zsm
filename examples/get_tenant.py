import json

import requests
from requests.auth import HTTPBasicAuth

api_host = 'http://localhost:80'
url = api_host + '/api/v1/tenants/c5c58b2057184781a5120334a9d1df29'

headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
}

response = requests.get(url=url, headers=headers,
                         auth=HTTPBasicAuth('admin@origin', 'a'))
print json.loads(response.text)
