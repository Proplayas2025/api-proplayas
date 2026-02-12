# Configuración del Sistema de Correos Electrónicos

## Descripción

El sistema de invitaciones de Proplayas envía correos electrónicos automáticos a los usuarios cuando son invitados a unirse como:
- **Líder de Nodo**: Invitado por un administrador
- **Miembro de Nodo**: Invitado por un líder de nodo

## Entornos

### Desarrollo (MailHog)

**MailHog** es un servidor SMTP de prueba que captura todos los correos enviados y los muestra en una interfaz web.

**Configuración en `.env`:**
```env
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@proplayas.org
FROM_NAME=Proplayas
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
```

**Acceso a MailHog:**
- Interfaz web: http://localhost:8025
- Puerto SMTP: 1025

**Uso:**
1. Inicia el stack de Docker:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. Envía una invitación desde el dashboard admin o mediante la API

3. Abre http://localhost:8025 para ver el correo capturado

4. El correo contiene un link de registro con el token JWT

### Producción (Gmail / SMTP Real)

**Configuración en `.env`:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Proplayas
ENVIRONMENT=production
FRONTEND_URL=https://proplayas.org
```

**Para Gmail:**
1. Habilita "Verificación en 2 pasos" en tu cuenta de Google
2. Genera una "Contraseña de aplicación" en: https://myaccount.google.com/apppasswords
3. Usa esa contraseña de 16 caracteres en `SMTP_PASSWORD`

**Para otros proveedores SMTP:**
- **SendGrid**: `smtp.sendgrid.net` puerto 587
- **Mailgun**: `smtp.mailgun.org` puerto 587
- **AWS SES**: `email-smtp.us-east-1.amazonaws.com` puerto 587

## Flujo de Invitaciones

### 1. Crear Invitación

**Endpoint:** `POST /api/invitations/node-leader` (admin) o `POST /api/invitations/member` (líder)

**Payload:**
```json
{
  "name": "Juan Pérez",
  "email": "juan@example.com",
  "node_type": "cientifico"  // Solo para node-leader
}
```

**Proceso:**
1. Valida que no exista invitación pendiente para ese email
2. Genera un código de nodo automáticamente (para node-leader)
3. Crea un token JWT con expiración de 7 días
4. Guarda la invitación en la base de datos
5. **Envía el correo electrónico** con el token
6. Devuelve el token al frontend (para compartir manualmente si es necesario)

### 2. Usuario Recibe Correo

El correo incluye:
- **Asunto**: "Invitación a Proplayas - Líder de Nodo" o "Miembro de Nodo"
- **Botón CTA**: Link directo a `/validate-invitation?token=...`
- **Descripción del rol** y responsabilidades
- **Validez**: 7 días
- **Diseño responsivo** compatible con todos los clientes de correo

### 3. Validar Token

**Endpoint:** `GET /api/invitations/{token}`

**Respuesta:**
```json
{
  "status": 200,
  "message": "Invitación válida",
  "data": {
    "name": "Juan Pérez",
    "email": "juan@example.com",
    "role_type": "node_leader",
    "node_type": "cientifico",
    "node_id": null
  }
}
```

### 4. Completar Registro

**Endpoint:** `POST /api/invitations/accept`

**Payload:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "email": "juan@example.com",
  "password": "base64_encoded_password",
  "username": "juanperez",
  "name": "Juan Pérez",
  // ... más datos según el rol
}
```

**Proceso:**
1. Valida el token y que no haya expirado
2. Verifica que el email coincida
3. Crea el usuario
4. Crea el nodo (si es node-leader) o asigna al nodo existente (si es member)
5. Marca la invitación como "accepted"
6. Genera códigos (node_code o member_code)

## Plantilla de Correo

La plantilla HTML incluye:

**Características:**
- ✅ Diseño responsivo
- ✅ Colores corporativos (cyan-700)
- ✅ Botón CTA destacado
- ✅ Fallback de texto plano
- ✅ Compatible con Gmail, Outlook, Apple Mail, etc.
- ✅ Mensajes personalizados según el rol

**Secciones:**
1. **Header**: Logo y nombre de Proplayas con gradiente
2. **Contenido principal**: 
   - Saludo personalizado
   - Descripción del rol
   - Beneficios/responsabilidades
3. **CTA**: Botón "Completar Registro"
4. **Link alternativo**: URL en texto plano si el botón no funciona
5. **Avisos**: Validez de 7 días, instrucciones de ignorar si no solicitó
6. **Footer**: Información de contacto y enlaces

## Logs y Debugging

El servicio de email registra cada operación:

```python
logger.info(f"EmailService initialized - Host: {smtp_host}:{smtp_port}")
logger.info(f"Sending email to {to_email} via {smtp_host}")
logger.info(f"Email sent successfully to {to_email}")
logger.error(f"Error sending email: {error}", exc_info=True)
```

**Ver logs en Docker:**
```bash
docker-compose -f docker-compose.dev.yml logs -f api
```

## Pruebas Manuales

### Test 1: Invitar Líder de Nodo

```bash
# 1. Login como admin
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@proplayas.org",
    "password": "base64_encoded_password"
  }'

# 2. Crear invitación
curl -X POST http://localhost:8080/api/invitations/node-leader \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Test Leader",
    "email": "leader@test.com",
    "node_type": "cientifico"
  }'

# 3. Ver correo en: http://localhost:8025
```

### Test 2: Invitar Miembro

```bash
# 1. Login como líder de nodo
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "leader@proplayas.org",
    "password": "base64_encoded_password"
  }'

# 2. Crear invitación
curl -X POST http://localhost:8080/api/invitations/member \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Test Member",
    "email": "member@test.com"
  }'

# 3. Ver correo en: http://localhost:8025
```

## Solución de Problemas

### Error: "Connection refused" al enviar correo

**Causa**: El servicio de MailHog no está corriendo o no es accesible.

**Solución:**
```bash
# Verificar que MailHog esté corriendo
docker-compose -f docker-compose.dev.yml ps

# Reiniciar el servicio
docker-compose -f docker-compose.dev.yml restart mailhog

# Ver logs de MailHog
docker-compose -f docker-compose.dev.yml logs -f mailhog
```

### Error: "No such host" o "Name resolution failed"

**Causa**: Configuración incorrecta del host SMTP.

**Solución:**
- En Docker: usar `SMTP_HOST=mailhog` (nombre del servicio)
- En local sin Docker: usar `SMTP_HOST=localhost`

### Los correos no aparecen en MailHog

**Verificar:**
1. ¿El endpoint de invitación devuelve éxito?
2. ¿Hay errores en los logs del API?
3. ¿MailHog está accesible en http://localhost:8025?
4. ¿Las variables de entorno están correctamente configuradas?

```bash
# Verificar configuración desde el contenedor
docker-compose -f docker-compose.dev.yml exec api env | grep SMTP
```

### Timeout al enviar correo

**Causa**: Puerto incorrecto o firewall bloqueando.

**Solución:**
- MailHog usa puerto **1025** (no 25, 587, ni 465)
- Verificar que el puerto esté expuesto en docker-compose.dev.yml
- Temporalmente aumentar el timeout en `email.py`: `timeout=30`

## Mejoras Futuras

- [ ] Plantillas para más tipos de correos (bienvenida, recuperación de contraseña)
- [ ] Sistema de colas para envío masivo (Celery + Redis)
- [ ] Tracking de apertura y clicks
- [ ] Opciones de idioma (i18n)
- [ ] Adjuntos (PDFs, documentos)
- [ ] Firma digital de correos (DKIM)
- [ ] Webhooks para notificaciones de rebote/spam
