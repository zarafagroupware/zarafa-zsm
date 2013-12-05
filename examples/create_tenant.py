import json

import requests
from requests.auth import HTTPBasicAuth

api_host = 'http://localhost:80'
url = api_host + '/api/v1/tenants/'

tenant = {
    'name': 'durka durka37',
}

data = json.dumps(tenant)
headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
}

response = requests.post(url=url, headers=headers, data=data,
                         auth=HTTPBasicAuth('admin@origin', 'a'))
created_tenant = json.loads(response.text)

print created_tenant.get('name'), created_tenant
