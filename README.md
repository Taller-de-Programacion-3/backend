# Backend component

Currently deployed at https://taller3-backend.herokuapp.com/

## Setup

Se requiere tener `python` y `pip` instalados además de una versión corriendo de PostgreSQL. Para el resto de las dependencias localmente correr:
```pip install -r requirements.txt```

Una vez instaladas tenemos que correr las migraciones:

```bash
export DB_URL=postgresql://<usuario postgres>:<contraseña>@localhost/<nombre base de datos>
alembic upgrade head
```

## Migraciones

Para generar una nueva migración correr el siguiente comando:

```bash
$ alembic revision -m "<Descripción del cambio>"
```

Se pueden tambien generar las migraciones en base a los modelos, para esto correr

```bash
export DB_URL=postgresql://<usuario postgres>:<contraseña>@localhost/<nombre db> 
alembic revision --autogenerate
```

## Levantar la app

Para levantar hay que tener generar un `.env` en base al `.env.example`.

```bash
export FLASK_ENV=development 
export FLASK_APP=app.py 

flask run
or 
python3 app.py
```
