# ✅ Sistema de Correos Electrónicos - CONFIGURACIÓN COMPLETADA

## 🎯 Resumen de Cambios

Se ha implementado completamente el sistema de envío de correos electrónicos para invitaciones de usuarios en Proplayas.

### Archivos Modificados/Creados:

1. **`app/core/config.py`** ✅
   - Agregada variable `ENVIRONMENT` para detectar desarrollo/producción
   - Configuración por defecto para MailHog (`mailhog:1025`)
   - Soporte para SMTP de producción

2. **`app/core/email.py`** ✅
   - Servicio completo de envío de correos con `aiosmtplib`
   - Plantillas HTML profesionales y responsivas
   - Detección automática de entorno (desarrollo no requiere autenticación)
   - Logging detallado de todas las operaciones
   - Plantillas diferenciadas para `node_leader` y `member`
   - Versión texto plano como fallback

3. **`docker-compose.dev.yml`** ✅
   - Agregadas variables de entorno SMTP al servicio `api`
   - Configuración para usar MailHog automáticamente

4. **`.env.example`** ✅
   - Documentación clara de variables para desarrollo y producción
   - Valores por defecto para MailHog

5. **`EMAIL_SETUP.md`** ✅
   - Documentación completa del sistema
   - Ejemplos de configuración para Gmail, SendGrid, AWS SES
   - Guía de troubleshooting

6. **`EMAIL_QUICKSTART.md`** ✅
   - Guía rápida de inicio
   - Pasos para probar el sistema
   - Comandos listos para copiar/pegar

7. **`test_email.py`** ✅
   - Script de prueba interactivo
   - Envía correos de prueba para ambos roles
   - Muestra configuración actual

## 🚀 Cómo Usar

### Primer Uso (Configuración Inicial):

```bash
# 1. Crear archivo .env desde el ejemplo
cd api-proplayas
cp .env.example .env

# 2. Levantar el stack con MailHog
docker-compose -f docker-compose.dev.yml up -d

# 3. Ejecutar prueba de correos
docker-compose -f docker-compose.dev.yml exec api python test_email.py

# 4. Ver correos en MailHog
# Abre http://localhost:8025 en tu navegador
```

### Uso Normal (Invitar Usuarios):

**Desde el Dashboard:**
1. Login como admin en http://localhost:3000
2. Dashboard > Nodos > Click "Añadir nodo"
3. Completar formulario (nombre, email, tipo de nodo)
4. El sistema automáticamente:
   - ✅ Genera el token JWT
   - ✅ Guarda invitación en BD
   - ✅ **Envía el correo**
   - ✅ Devuelve link para compartir manualmente (respaldo)

**Verificar en MailHog:**
- Abre http://localhost:8025
- Verás el correo con diseño profesional
- Click en el botón "Completar Registro" para probar el flujo

## 📧 Plantilla de Correo

La plantilla incluye:
- ✅ Header con gradiente cyan corporativo
- ✅ Logo "Proplayas"
- ✅ Mensaje personalizado según rol (líder vs miembro)
- ✅ Botón CTA grande y visible
- ✅ Link alternativo en texto
- ✅ Aviso de expiración (7 días)
- ✅ Footer con información de contacto
- ✅ Diseño responsivo (funciona en móviles)
- ✅ Compatible con todos los clientes de correo

## 🔧 Configuración por Entorno

### Desarrollo (actual) - MailHog:
```env
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@proplayas.org
ENVIRONMENT=development
```
- ✅ NO requiere autenticación
- ✅ NO requiere TLS
- ✅ Todos los correos se capturan localmente
- ✅ Interfaz web en http://localhost:8025

### Producción - Gmail:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password-de-16-caracteres
FROM_EMAIL=tu-email@gmail.com
ENVIRONMENT=production
```
- ✅ Requiere "Contraseña de aplicación" de Google
- ✅ Usa STARTTLS automáticamente
- ✅ Los correos se envían realmente

### Producción - Otros Proveedores:

**SendGrid:**
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=tu-sendgrid-api-key
```

**Mailgun:**
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@tu-dominio.mailgun.org
SMTP_PASSWORD=tu-mailgun-password
```

**AWS SES:**
```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=tu-ses-smtp-username
SMTP_PASSWORD=tu-ses-smtp-password
```

## 🧪 Testing

### Test Automático:
```bash
# Dentro del contenedor
docker-compose -f docker-compose.dev.yml exec api python test_email.py

# Local (si tienes Python configurado)
python test_email.py
```

### Test Manual desde el Dashboard:
1. Login como admin
2. Crear invitación para líder de nodo
3. Verificar correo en http://localhost:8025
4. Copiar token del correo
5. Abrir link de registro en navegador
6. Completar formulario de registro
7. Verificar que el usuario se creó correctamente

### Test desde la API (curl):
```bash
# 1. Login como admin
TOKEN=$(curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@proplayas.org","password":"base64_password"}' \
  | jq -r '.data.token')

# 2. Crear invitación
curl -X POST http://localhost:8080/api/invitations/node-leader \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Leader",
    "email": "test@example.com",
    "node_type": "cientifico"
  }'

# 3. Ver correo en http://localhost:8025
```

## 📊 Logs y Monitoreo

**Ver logs en tiempo real:**
```bash
docker-compose -f docker-compose.dev.yml logs -f api | grep -i email
```

**Logs exitosos (ejemplo):**
```
EmailService initialized - Host: mailhog:1025, Environment: development
Sending email to user@example.com via mailhog:1025 (no auth)
Email sent successfully to user@example.com
```

**Logs de error (ejemplo):**
```
Error sending email to user@example.com: Connection refused
```

## ⚠️ Notas Importantes

1. **Security**: En producción, NUNCA commitear archivos `.env` con credenciales reales al repositorio

2. **MailHog**: Solo para desarrollo. Los correos NO salen a internet real.

3. **Token JWT**: Cada token es único y expira en 7 días exactamente.

4. **Validación de email**: El sistema valida que:
   - No exista invitación pendiente para ese email
   - No exista usuario con ese email
   - El token no haya expirado
   - El email del token coincida con el del formulario

5. **Códigos automáticos**: 
   - Node codes se generan automáticamente: `CIE-01`, `CIE-02`, etc.
   - Member codes heredan del nodo: `CIE-01-1`, `CIE-01-2`, etc.

## ✨ Características Implementadas

- ✅ Envío automático de correos en invitaciones
- ✅ Plantillas HTML profesionales y responsivas
- ✅ Detección automática de entorno (dev/prod)
- ✅ Logging completo de operaciones
- ✅ Soporte para múltiples roles (líder, miembro)
- ✅ Mensajes personalizados por rol
- ✅ Fallback a texto plano
- ✅ Compatible con MailHog para desarrollo
- ✅ Compatible con SMTP reales para producción
- ✅ Timeout configurable
- ✅ Manejo robusto de errores

## 🎉 ¡Todo Listo!

El sistema de correos está completamente funcional y listo para usar.

**Próximos pasos:**
1. Prueba el envío con MailHog
2. Verifica que los correos se vean correctamente
3. Prueba el flujo completo de invitación → registro
4. Cuando estés listo para producción, actualiza `.env` con credenciales reales

**Documentación:**
- Guía rápida: [EMAIL_QUICKSTART.md](./EMAIL_QUICKSTART.md)
- Guía completa: [EMAIL_SETUP.md](./EMAIL_SETUP.md)
- Script de prueba: [test_email.py](./test_email.py)
