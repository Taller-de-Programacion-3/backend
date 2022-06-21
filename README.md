# Backend component

Currently deployed at https://taller3-backend.herokuapp.com/

## Setup

Se requiere tener `python` y `pip` instalados ademaás de una versión corriendo de PostgreSQL. Para el resto de las dependencias localmente correr:
```pip install -r requirements.txt```

Una vez instaladas tenemos que correr las migraciones:

```bash
DB_URL=postgresql://<usuario postgres>:<contraseña>@localhost/<nombre base de datos> alembic upgrade head
```

## Migraciones

Para generar una nueva migración correr el siguiente comando:

```bash
$ alembic revision -m "<Descripción del cambio>"
```
