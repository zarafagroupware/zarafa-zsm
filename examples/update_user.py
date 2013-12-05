import json

import requests
from requests.auth import HTTPBasicAuth

api_host = 'http://localhost:80'
user_uri = '/api/v1/tenants/c5c58b2057184781a5120334a9d1df29/users/76e23a13fd5b41b78367ba6275479740/'
url = api_host + user_uri

headers = {
    'accept': 'application/json',
    'content-type': 'application/json',
}

response = requests.get(url=url, headers=headers,
                         auth=HTTPBasicAuth('admin@origin', 'a'))

user = json.loads(response.text)
user['title'] = (user['title'] or '') + 'title'
data = json.dumps(user)

response = requests.put(url=url, headers=headers, data=data,
                         auth=HTTPBasicAuth('admin@origin', 'a'))
print response
