from libzsm.rest_client.utils import get_api

api = get_api()

for tenant in api.all_tenant():
    print 'TENANT', tenant.name
    for user in api.all_user(tenant=tenant):
        print '    USER', user.name
    for group in api.all_group(tenant=tenant):
        print '    GROUP', group.name
    for contact in api.all_contact(tenant=tenant):
        print '    CONTACT', group.name

for server in api.all_server():
    print 'SERVER', server.name
