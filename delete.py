# -*- coding: utf-8 -*-
#!/usr/bin/python

import routeros_api
ip4='10.57.10.111'
connection = routeros_api.RouterOsApiPool(ip4, username='admin', password='admin', port=8728, plaintext_login=True )
api = connection.get_api()
list_queues = api.get_resource('/ip/firewall/address-list')

pole=list_queues.get()
for prvek in pole:
    print(prvek)
    list_queues.remove(id=prvek['id'])

    print(id)
connection.disconnect()

# otestovat rychlost zápisu cca 10K ip adress
# mazání přes ID - otestovat 10K
# Otestovat rychlost výpisu 10k záznamů



connection.disconnect()
