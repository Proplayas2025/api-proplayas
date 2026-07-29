"""Base declarativa única para todos los modelos ORM.

`Base` se define en `database.py` (junto al engine y la sesión) y aquí solo se
reexporta, de modo que todos los modelos compartan el mismo registry de
SQLAlchemy. Declarar una segunda base rompe la resolución de relaciones
(`expression 'Node' failed to locate a name`) y deja a Alembic sin un
`metadata` único desde el cual autogenerar migraciones.
"""
from database import Base

__all__ = ["Base"]
