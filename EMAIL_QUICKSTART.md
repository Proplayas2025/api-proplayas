# Guía Rápida: Prueba del Sistema de Correos

## 🚀 Inicio Rápido

### 1. Levantar el stack de desarrollo con MailHog

```bash
cd api-proplayas
docker-compose -f docker-compose.dev.yml up -d
```

Esto iniciará:
- ✅ API en http://localhost:8080
- ✅ PostgreSQL en puerto 5433
- ✅ MailHog en http://localhost:8025

### 2. Verificar que todos los servicios estén corriendo

```bash
docker-compose -f docker-compose.dev.yml ps
```

Deberías ver 3 contenedores activos:
- `proplayas-api-dev`
- `proplayas-postgres-dev`
- `proplayas-mailhog`

### 3. Ejecutar prueba de correo

**Opción A: Desde dentro del contenedor (recomendado)**

```bash
docker-compose -f docker-compose.dev.yml exec api python test_email.py
```

**Opción B: Directamente si tienes Python local**

```bash
# Configurar variables de entorno
export SMTP_HOST=localhost
export SMTP_PORT=1025
export FROM_EMAIL=noreply@proplayas.org
export ENVIRONMENT=development
export FRONTEND_URL=http://localhost:3000

# Ejecutar el script
python test_email.py
```

### 4. Ver los correos en MailHog

Abre tu navegador en: **http://localhost:8025**

Deberías ver 2 correos recibidos:
- 📧 Invitación como Líder de Nodo
- 📧 Invitación como Miembro

### 5. Probar desde el Dashboard (E2E)

1. Abre http://localhost:3000
2. Login como admin
3. Ve a **Dashboard > Nodos**
4. Click en **"Añadir nodo"** o **"Invitar líder"**
5. Completa el formulario con:
   - Nombre: `Juan Pérez`
   - Email: `juan@test.com`
   - Tipo de nodo: `Científico`
6. Enviar invitación
7. Verifica en http://localhost:8025 que llegó el correo

### 6. Flujo completo de invitación

```
Admin Dashboard
    ↓
Crear invitación (POST /api/invitations/node-leader)
    ↓
Backend genera token JWT + guarda en BD
    ↓
Envía correo con token a juan@test.com
    ↓
MailHog captura el correo (en desarrollo)
    ↓
Usuario recibe correo con link:
http://localhost:3000/validate-invitation?token=xxxxx
    ↓
Usuario hace click en el link
    ↓
Frontend valida token (GET /api/invitations/{token})
    ↓
Usuario completa formulario de registro
    ↓
Backend crea usuario + nodo (POST /api/invitations/accept)
    ↓
Usuario puede hacer login
```

## ✅ Verificación de Éxito

**Logs del API:**
```bash
docker-compose -f docker-compose.dev.yml logs -f api | grep -i email
```

Deberías ver:
```
EmailService initialized - Host: mailhog:1025, Environment: development
Sending email to test@example.com via mailhog:1025 (no auth)
Email sent successfully to test@example.com
```

**MailHog UI:**
- Ve a http://localhost:8025
- Deberías ver correos con:
  - ✅ Asunto: "Invitación a Proplayas - Líder de Nodo"
  - ✅ Remitente: Proplayas <noreply@proplayas.org>
  - ✅ Diseño HTML profesional con botón azul
  - ✅ Link funcional a `/validate-invitation?token=...`

## 🐛 Troubleshooting

### No se envían correos

1. Verificar que MailHog esté corriendo:
   ```bash
   docker-compose -f docker-compose.dev.yml ps mailhog
   ```

2. Ver logs del API:
   ```bash
   docker-compose -f docker-compose.dev.yml logs api
   ```

3. Reiniciar servicios:
   ```bash
   docker-compose -f docker-compose.dev.yml restart
   ```

### Error "Connection refused"

El contenedor de API no puede conectarse a MailHog.

**Solución:**
```bash
# Verificar red de Docker
docker network ls
docker network inspect api-proplayas_proplayas-network

# Verificar que ambos contenedores estén en la misma red
```

### Variables de entorno no se cargan

Crea un archivo `.env` en la raíz de `api-proplayas/`:

```bash
cp .env.example .env
```

Edita `.env` y asegúrate de tener:
```env
SMTP_HOST=mailhog
SMTP_PORT=1025
FROM_EMAIL=noreply@proplayas.org
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
```

### Los correos llegan pero sin formato

Verifica en MailHog:
1. Click en el correo
2. Tab "HTML" - debe mostrar el diseño con colores
3. Tab "Plain Text" - debe tener versión de texto

Si solo ves texto plano, revisa que la plantilla HTML se esté generando correctamente en `core/email.py`.

## 📝 Notas

- **Desarrollo**: MailHog captura TODOS los correos, ninguno sale realmente a internet
- **Producción**: Configurar con Gmail/SendGrid/otro SMTP real
- **Seguridad**: Nunca commitear credenciales reales al repositorio
- **Token JWT**: Válido por 7 días, después expira automáticamente

## 🔗 Enlaces Útiles

- **API Docs**: http://localhost:8080/docs
- **MailHog UI**: http://localhost:8025
- **Frontend**: http://localhost:3000
- **Documentación completa**: [EMAIL_SETUP.md](./EMAIL_SETUP.md)
