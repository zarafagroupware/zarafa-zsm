import json

import requests
from requests.auth import HTTPBasicAuth

api_host = 'http://localhost:8000'
tenant_uri = '/api/v1/tenants/681732aad0ed4abdb0f511e2cb8accf2/'
url = '%s%susers/' % (api_host, tenant_uri)

headers = {
    'accept': 'application/json',
}
response = requests.get(url, headers=headers, auth=HTTPBasicAuth('admin@origin', 'a'))
print response.text
users = json.loads(response.text)
