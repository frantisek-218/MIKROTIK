# -*- coding: utf-8 -*-
#!/usr/bin/python

import routeros_api
from random import randint
from datetime import datetime, date
# zdroj https://github.com/socialwifi/RouterOS-api/blob/master/README.md

connection = routeros_api.RouterOsApiPool('10.57.10.111', username='admin', password='admin', port=8728, plaintext_login=True )
api = connection.get_api()

# vypsani aktualniho adresslistu
list_queues = api.get_resource('/ip/firewall/address-list')
#print(list_queues.get())

# pridani adresy

for i in range(1,10001):
    def generate_random_ip():
        return '.'.join(
            str(randint(0, 255)) for _ in range(4)
        )
    random_ip = generate_random_ip()
    list_queues.add(address=random_ip, comment='TEST',  list='sentinel')
    print(id)





# otestovat rychlost zápisu cca 10K ip adress
# mazání přes ID - otestovat 10K
# Otestovat rychlost výpisu 10k záznamů



connection.disconnect()
