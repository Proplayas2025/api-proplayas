# Proplayas API

FastAPI backend para el sistema de gestión de nodos de Proplayas.

## Estructura del Proyecto

La API sigue una arquitectura en capas estricta:

```
routers → services → repositories → models
```

- **routers**: capa fina. Validan la entrada, resuelven el usuario autenticado y arman el envelope de respuesta. Sin lógica de negocio.
- **services**: toda la lógica de negocio (validaciones, permisos, reglas). Reciben repositorios inyectados y devuelven schemas Pydantic, nunca modelos ORM.
- **repositories**: solo consultas y persistencia. Devuelven modelos ORM o `None`.
- **models**: SQLAlchemy. Comparten una única `Base` (`database.py`, reexportada en `models/base.py`).

```
api-proplayas/
├── app/
│   ├── core/              # Configuración e infraestructura transversal
│   │   ├── config.py
│   │   ├── security.py    # JWT, hashing, dependencias de autenticación
│   │   ├── email.py
│   │   ├── image.py       # Optimización a WebP
│   │   ├── storage.py     # Guardado de imágenes y documentos
│   │   └── exceptions.py  # AppError (envelope de error de negocio)
│   ├── models/            # Modelos SQLAlchemy
│   ├── schemas/           # Modelos Pydantic (contrato con el frontend)
│   │   └── common.py      # Page, PageMeta, Result
│   ├── repositories/      # Acceso a datos (queries)
│   ├── services/          # Lógica de negocio
│   ├── routers/           # Endpoints de la API
│   ├── migrations/        # Migraciones Alembic
│   ├── dependencies.py    # Inyección de repositorios y servicios
│   ├── enums.py           # Enums del dominio (fuente única)
│   ├── database.py        # Engine, sesión y Base
│   ├── alembic.ini
│   └── main.py            # Aplicación FastAPI
├── storage/               # Archivos subidos
├── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── requirements.txt
└── README.md
```

## Roles y Permisos

- **Admin**: Control total del sistema
- **Node Leader**: Gestión de su nodo y miembros
- **Member**: Creación y edición de contenido

## Desarrollo Local

### Con Docker (Recomendado)

```bash
# Copiar variables de entorno
cp .env.example .env

# Iniciar en modo desarrollo
docker-compose -f docker-compose.dev.yml up -d

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f api

# Detener
docker-compose -f docker-compose.dev.yml down
```

### Sin Docker

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurar variables de entorno
cp .env.example .env

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Sistema de Correos Electrónicos 📧

El sistema envía invitaciones automáticas por correo cuando se invita a nuevos usuarios.

### Desarrollo (MailHog)

MailHog captura todos los correos localmente para pruebas:

```bash
# Ya incluido en docker-compose.dev.yml
# Interfaz web: http://localhost:8025
# Puerto SMTP: 1025

# Probar envío de correos
docker-compose -f docker-compose.dev.yml exec api python test_email.py
```

**Configuración en `.env` para desarrollo:**
```env
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@proplayas.org
ENVIRONMENT=development
```

### Producción (Gmail/SMTP Real)

**Configuración en `.env` para producción:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password
FROM_EMAIL=tu-email@gmail.com
ENVIRONMENT=production
```

### Documentación Completa

- 🚀 **Guía rápida**: [EMAIL_QUICKSTART.md](./EMAIL_QUICKSTART.md)
- 📚 **Documentación completa**: [EMAIL_SETUP.md](./EMAIL_SETUP.md)
- 📝 **Resumen de implementación**: [EMAIL_IMPLEMENTATION_SUMMARY.md](./EMAIL_IMPLEMENTATION_SUMMARY.md)

## Migraciones de Base de Datos (Alembic)

El esquema se versiona con Alembic. **No se crean tablas con `create_all`**: todo cambio
en `app/models/` debe pasar por una migración.

```bash
# Aplicar migraciones pendientes (primera vez y en cada despliegue)
make db-upgrade

# Generar una migración tras cambiar los modelos (revísala antes de aplicarla)
make db-migrate MSG="agrega campo x a users"

# Ver estado e historial
make db-current
make db-history

# Revertir la última migración
make db-downgrade

# BD ya existente creada antes de Alembic: marcarla como migrada sin ejecutar DDL
make db-stamp
```

Los archivos generados quedan en `app/migrations/versions/`. Flujo habitual:

1. Modificar el modelo en `app/models/`.
2. `make db-migrate MSG="..."`.
3. Revisar el archivo generado (Alembic no resuelve bien FKs circulares ni tipos ENUM).
4. `make db-upgrade`.
5. Commitear la migración junto al cambio de modelo.

En producción, ejecutar `make db-upgrade ENV=prod` tras desplegar la nueva imagen.

Ver [COMPATIBILITY.md](COMPATIBILITY.md) para detalles de compatibilidad con el frontend.

## API Endpoints

### Autenticación
- `POST /api/login` - Login
- `POST /api/register` - Registro con invitación
- `POST /api/logout` - Logout

### Usuarios
- `GET /api/users` - Lista usuarios (admin)
- `GET /api/user/{id}` - Obtener usuario
- `PUT /api/user/{id}` - Actualizar usuario
- `DELETE /api/user/{id}` - Eliminar usuario (admin)

### Nodos
- `GET /api/nodes` - Lista nodos (público)
- `GET /api/node/{code}` - Obtener nodo
- `GET /api/node/members/{code}` - Miembros de nodo
- `POST /api/node` - Crear nodo (admin)
- `PUT /api/node/{id}` - Actualizar nodo

### Contenido
- `GET /api/content` - Lista contenido
- `GET /api/content/{id}` - Obtener contenido
- `POST /api/content` - Crear contenido
- `PUT /api/content/{id}` - Actualizar contenido
- `DELETE /api/content/{id}` - Eliminar contenido

### Invitaciones
- `POST /api/invitation` - Enviar invitación
- `POST /api/invitation/validate` - Validar token
- `GET /api/invitations` - Lista invitaciones

## Testing

```bash
pytest
pytest --cov=app tests/
```

## Producción

```bash
# Construir y iniciar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

## Variables de Entorno

Ver `.env.example` para todas las variables necesarias.

## Documentación API

Una vez iniciado el servidor:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
