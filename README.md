# **Mikrotik**

Mikrotik Virtual machine RouterOS, připojení přes síťový most na virtual machine skrze WinBox.





## Příkazy:

``` 
python3 -m venv .venv
source .venv/bin/activate
pip install requirements.txt
```
## Migrate příkazy:

``` 
flask db init
flask db migrate
flask db upgrade
```
## Tutoriál pro zprovoznění mikrotiku skrze VirtualBox:
  ```
  https://www.youtube.com/watch?v=0FStQTNAgi4
  ```

## Knihovny:

**SQLAlchemy**
**Flask**

## Hotovo:
  Flask-appka(musí se dodělat api)| naplnění mikrotiku z https://view.sentinel.turris.cz/dynfw/ - chybí dodělat delete funkce| 


## Poznámky:
Zatím jen randomIp generátor pro naplnění databáze mikrotiku, propojení, flask appka, frontend, edit ip adress.  
IP našeho mikrotiku: 10.57.10.111/24

