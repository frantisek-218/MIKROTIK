# **Mikrotik**

Flask apka, dá se zapisovat do databáze, upravovat zápisy, mazat zápisy. Spojení se sentinelem již hotovo, data se zapisují do databáze. 


## Příkazy:

``` 
python3 -m venv .venv
source .venv/bin/activate
pip install requirements.txt
```

## Knihovny:

**SQLAlchemy**
**Flask**


## Poznámky:

Připojil jsem client.py file. Jen nejde delete, jinak se ze sentinelu do databáze data zapisují. Dali jsme do toho dnes všechno... Autentifikace se tedy bude dělat nakonec. Ještě doděláme propojení s mikrotikem.
