import json

import requests
from requests.auth import HTTPBasicAuth

api_host = 'http://localhost:80'
tenant_uri = '/api/v1/tenants/ee1fdad19d5f4da69efd7dec3855ed46/'
url = api_host + tenant_uri

headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
}

response = requests.delete(url=url, headers=headers,
                         auth=HTTPBasicAuth('admin@origin', 'a'))
print response
