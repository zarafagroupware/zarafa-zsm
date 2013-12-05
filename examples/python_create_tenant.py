from libzsm.rest_client.utils import get_api

api = get_api()

tenant = api.create_tenant(initial={'name': 'banuetuhanoue'})
print 'tenant %s created' % tenant.name
