# -*- coding: utf-8 -*-
#!/usr/bin/python

import routeros_api
from random import randint
# zdroj https://github.com/socialwifi/RouterOS-api/blob/master/README.md

connection = routeros_api.RouterOsApiPool('192.168.0.222', username='admin', password='admin', port=8728, plaintext_login=True )
api = connection.get_api()

# vypsani aktualniho adresslistu
list_queues = api.get_resource('/ip/firewall/address-list')
#print(list_queues.get())

#smazani adresy
print("zadej ip: ")
ipToDelete = input()
i = 0


pole=list_queues.get()
for prvek in pole:
    if prvek['address'] == ipToDelete:
        break
    i+= 1
print(list_queues.get()[i]['id'])
print(list_queues.get()[i]['address'])
idToDelete = list_queues.get()[i]['id']
list_queues.remove(id=idToDelete)





# otestovat rychlost zápisu cca 10K ip adress
# mazání přes ID - otestovat 10K
# Otestovat rychlost výpisu 10k záznamů



connection.disconnect()