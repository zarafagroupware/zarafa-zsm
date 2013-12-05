import json

import requests
from requests.auth import HTTPBasicAuth

api_host = 'http://localhost:8000'
tenant_uri = '/api/v1/tenants/681732aad0ed4abdb0f511e2cb8accf2/'
url = '%s%susers/' % (api_host, tenant_uri)

user = {
    'mail': 'john.doe@example.com',
    'name': 'John Doe',
    'surname': 'Doe',
    'tenant': tenant_uri,
    'userServer': '/api/v1/servers/36443f113ac44150aa3732f28e6bf565/',
    'username': 'jdoe',
}

data = json.dumps(user)
headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
}

response = requests.post(url=url, headers=headers, data=data,
                         auth=HTTPBasicAuth('admin@origin', 'a'))
created_user = json.loads(response.text)
