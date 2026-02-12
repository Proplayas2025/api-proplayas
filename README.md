# Proplayas API

FastAPI backend para el sistema de gestión de nodos de Proplayas.

## Estructura del Proyecto

```
api-proplayas/
├── app/
│   ├── core/              # Configuración, seguridad, servicios
│   │   ├── config.py
│   │   ├── security.py
│   │   └── email.py
│   ├── models/            # Modelos SQLAlchemy
│   │   ├── user.py
│   │   ├── node.py
│   │   ├── content.py
│   │   ├── social_link.py
│   │   └── invitation.py
│   ├── schemas/           # Modelos Pydantic
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── node.py
│   │   ├── content.py
│   │   └── invitation.py
│   ├── routes/            # Endpoints de la API
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── nodes.py
│   │   ├── content.py
│   │   └── invitations.py
│   ├── database.py        # Configuración de base de datos
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

## Migraciones de Base de Datos

```bash
# Inicializar tablas (primera vez)
docker exec -it proplayas-api-dev python init_db.py

# O desde el directorio app en local
cd app && python init_db.py
```

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
