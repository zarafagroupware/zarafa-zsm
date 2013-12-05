import json

import requests
from requests.auth import HTTPBasicAuth

api_host = 'http://localhost:80'
tenant_uri = '/api/v1/tenants/c2387b2bcbb24e849cda5bb8e51f78c3/'
url = '%s%susers/' % (api_host, tenant_uri)

user = {
    'mail': 'joep.doe3@example.com',
    'name': 'Joep Doe3',
    'surname': 'Doe3',
    'tenant': tenant_uri,
    'userServer': '/api/v1/servers/4db3a5241c134c05b24d18bb983d6a7e/',
    'username': 'joepdoe30',
}

data = json.dumps(user)
headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
}

response = requests.post(url=url, headers=headers, data=data,
                         auth=HTTPBasicAuth('admin@origin', 'a'))
created_user = json.loads(response.text)
print created_user
