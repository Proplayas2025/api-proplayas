# Makefile para Proplayas API
.PHONY: help build build-dev dev dev-build dev-down prod prod-build down stop stop-dev logs logs-api logs-db logs-mail db db-init db-migrate db-upgrade db-downgrade db-current db-history db-stamp db-seed db-populate db-clean db-reset shell-api clean info

# Variables
COMPOSE_FILE = docker-compose.yml
COMPOSE_DEV_FILE = docker-compose.dev.yml

# Detección automática de entorno basándose en contenedores corriendo
ENV ?= $(shell docker ps --format '{{.Names}}' | grep -q 'proplayas-api-dev' && echo "dev" || echo "prod")

# Contenedores según entorno
ifeq ($(ENV),dev)
	APP_CONTAINER = proplayas-api-dev
	DB_CONTAINER = proplayas-postgres-dev
	MAIL_CONTAINER = proplayas-mailhog
	COMPOSE = docker compose -f $(COMPOSE_DEV_FILE)
else
	APP_CONTAINER = proplayas-api
	DB_CONTAINER = proplayas-postgres
	COMPOSE = docker compose -f $(COMPOSE_FILE)
endif

# Ayuda
help:
	@echo "🌊 Proplayas API - Comandos disponibles"
	@echo ""
	@echo "📦 Construcción:"
	@echo "  make build          - Construir imágenes (producción)"
	@echo "  make build-dev      - Construir imágenes (desarrollo)"
	@echo ""
	@echo "🚀 Desarrollo:"
	@echo "  make dev            - Iniciar en modo desarrollo"
	@echo "  make dev-build      - Iniciar en desarrollo y construir"
	@echo "  make dev-down       - Detener desarrollo"
	@echo "  make stop-dev       - Pausar desarrollo"
	@echo ""
	@echo "🏭 Producción:"
	@echo "  make prod           - Iniciar en producción"
	@echo "  make prod-build     - Iniciar en producción y construir"
	@echo "  make down           - Detener producción"
	@echo "  make stop           - Pausar producción"
	@echo ""
	@echo "📊 Logs:"
	@echo "  make logs           - Ver logs (auto-detecta entorno)"
	@echo "  make logs-api       - Ver logs de la API"
	@echo "  make logs-db        - Ver logs de PostgreSQL"
	@echo "  make logs-mail      - Ver logs de MailHog (dev)"
	@echo ""
	@echo "🗄️  Base de datos y migraciones:"
	@echo "  make db             - Conectar a PostgreSQL"
	@echo "  make db-init        - Inicializar BD (aplica migraciones)"
	@echo "  make db-migrate MSG='...' - Generar migración desde los modelos"
	@echo "  make db-upgrade     - Aplicar migraciones pendientes"
	@echo "  make db-downgrade   - Revertir la última migración"
	@echo "  make db-current     - Ver revisión actual"
	@echo "  make db-history     - Ver historial de migraciones"
	@echo "  make db-stamp [REV=rev_id] - Marcar BD existente como migrada (sin DDL, default: head)"
	@echo ""
	@echo "🔧 Utilidades:"
	@echo "  make db-seed        - Poblar BD con datos de prueba"
	@echo "  make db-populate    - Poblar BD desde nodes.csv y users.csv"
	@echo "  make db-clean       - Limpiar BD (eliminar todo)"
	@echo "  make db-reset       - Reset completo (clean + init + seed)"
	@echo "  make shell-api      - Shell en contenedor API"
	@echo "  make clean          - Limpiar contenedores y volúmenes"
	@echo "  make info           - Información del entorno"
	@echo ""
	@echo "📌 Variables:"
	@echo "  ENV=dev/prod        - Especificar entorno manualmente"
	@echo ""
	@echo "💡 Nota: El entorno se detecta automáticamente según contenedores corriendo"
	@echo "   Si hay problemas, usa: make info (para ver estado actual)"

# Construcción
build:
	docker compose -f $(COMPOSE_FILE) build

build-dev:
	docker compose -f $(COMPOSE_DEV_FILE) build

# Desarrollo
dev:
	@echo "🚀 Iniciando Proplayas API en modo desarrollo..."
	docker compose -f $(COMPOSE_DEV_FILE) up -d
	@echo "⏳ Esperando a que PostgreSQL esté listo..."
	@bash -c 'until docker exec proplayas-postgres-dev pg_isready -U proplayas > /dev/null 2>&1; do echo -n "."; sleep 1; done; echo ""'
	@echo "✅ PostgreSQL listo"
	@echo "✅ API disponible en http://localhost:8080"
	@echo "📧 MailHog disponible en http://localhost:8025"
	@echo "📖 Docs disponibles en http://localhost:8080/api/docs"

dev-build:
	@echo "🔨 Construyendo e iniciando en modo desarrollo..."
	docker compose -f $(COMPOSE_DEV_FILE) up -d --build

dev-down:
	@echo "🛑 Deteniendo servicios de desarrollo..."
	docker compose -f $(COMPOSE_DEV_FILE) down

# Producción
prod:
	@echo "🚀 Iniciando Proplayas API en producción..."
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "⏳ Esperando a que PostgreSQL esté listo..."
	@bash -c 'until docker exec proplayas-postgres pg_isready -U proplayas > /dev/null 2>&1; do echo -n "."; sleep 1; done; echo ""'
	@echo "✅ PostgreSQL listo"
	@echo "✅ API disponible en http://localhost:8080"
	@echo "📖 Docs disponibles en http://localhost:8080/api/docs"

prod-build:
	@echo "🔨 Construyendo e iniciando en producción..."
	docker compose -f $(COMPOSE_FILE) up -d --build

down:
	@echo "🛑 Deteniendo servicios de producción..."
	docker compose -f $(COMPOSE_FILE) down

stop:
	docker compose -f $(COMPOSE_FILE) stop

stop-dev:
	docker compose -f $(COMPOSE_DEV_FILE) stop

# Logs
logs:
	@echo "📋 Mostrando logs ($(ENV))..."
	@if [ "$(ENV)" = "dev" ]; then \
		docker compose -f $(COMPOSE_DEV_FILE) logs -f; \
	else \
		docker compose -f $(COMPOSE_FILE) logs -f; \
	fi

logs-api:
	@echo "📋 Logs de API ($(APP_CONTAINER))..."
	docker logs -f $(APP_CONTAINER)

logs-db:
	@echo "📋 Logs de PostgreSQL ($(DB_CONTAINER))..."
	docker logs -f $(DB_CONTAINER)

logs-mail:
	@if [ "$(ENV)" = "dev" ]; then \
		echo "📋 Logs de MailHog..."; \
		docker logs -f $(MAIL_CONTAINER); \
	else \
		echo "⚠️  MailHog solo disponible en desarrollo"; \
	fi

# Acceso a servicios
db:
	@echo "🔗 Conectando a PostgreSQL ($(ENV))..."
	@echo "Usuario: proplayas | Base de datos: proplayas_db"
	docker exec -it $(DB_CONTAINER) psql -U proplayas -d proplayas_db

# Gestión de base de datos
db-init:
	@echo "🗄️  Inicializando base de datos (aplicando migraciones)..."
	@$(MAKE) db-upgrade
	@echo "✅ Base de datos inicializada"

# Migraciones (Alembic)
db-migrate:
	@if [ -z "$(MSG)" ]; then \
		echo "⚠️  Usa: make db-migrate MSG='descripcion del cambio'"; \
		exit 1; \
	fi
	@echo "📝 Generando migración: $(MSG)"
	docker exec $(APP_CONTAINER) alembic revision --autogenerate -m "$(MSG)"
	@echo "✅ Migración generada en app/migrations/versions/ (revísala antes de aplicarla)"

db-upgrade:
	@echo "⬆️  Aplicando migraciones pendientes..."
	docker exec $(APP_CONTAINER) alembic upgrade head
	@echo "✅ Migraciones aplicadas"

db-downgrade:
	@echo "⬇️  Revirtiendo una migración..."
	docker exec $(APP_CONTAINER) alembic downgrade -1

db-current:
	@echo "📍 Revisión actual de la base de datos:"
	docker exec $(APP_CONTAINER) alembic current

db-history:
	@echo "📜 Historial de migraciones:"
	docker exec $(APP_CONTAINER) alembic history --verbose

db-stamp:
	@echo "🏷️  Marcando la BD como migrada en $(if $(REV),$(REV),head) (sin ejecutar DDL)..."
	docker exec $(APP_CONTAINER) alembic stamp $(if $(REV),$(REV),head)

db-seed:
	@echo "🌱 Sembrando datos de prueba..."
	@echo "📦 Usando contenedor: $(APP_CONTAINER)"
	@if ! docker ps --format '{{.Names}}' | grep -q '^$(APP_CONTAINER)$$'; then \
		echo "❌ Error: Contenedor $(APP_CONTAINER) no está corriendo"; \
		echo "💡 Inicia el entorno con: make dev"; \
		exit 1; \
	fi
	docker exec -it $(APP_CONTAINER) python seed.py
	@echo "✅ Datos de prueba insertados"

db-populate:
	@echo "📥 Poblando BD desde nodes.csv y users.csv..."
	@echo "📦 Usando contenedor: $(APP_CONTAINER)"
	@if ! docker ps --format '{{.Names}}' | grep -q '^$(APP_CONTAINER)$$'; then \
		echo "❌ Error: Contenedor $(APP_CONTAINER) no está corriendo"; \
		echo "💡 Inicia el entorno con: make dev"; \
		exit 1; \
	fi
	docker exec -it $(APP_CONTAINER) python load_data_postgres.py
	@echo "✅ BD poblada con datos de CSVs"

db-clean:
	@echo "🧹 Limpiando base de datos..."
	@echo "⚠️  Esta acción eliminará TODAS las tablas y datos."
	@read -p "¿Estás seguro? (escriba 'yes' para confirmar): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker exec -it $(DB_CONTAINER) psql -U proplayas -d proplayas_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO proplayas; GRANT ALL ON SCHEMA public TO public;"; \
		echo "✅ Base de datos limpiada"; \
	else \
		echo "❌ Operación cancelada"; \
	fi

db-reset:
	@echo "🔄 Reiniciando base de datos (clean + init + seed)..."
	@$(MAKE) db-clean
	@$(MAKE) db-init
	@$(MAKE) db-seed
	@echo "✅ Base de datos reiniciada completamente"

shell-api:
	@echo "🐚 Accediendo a shell de API ($(APP_CONTAINER))..."
	docker exec -it $(APP_CONTAINER) /bin/bash

# Limpieza
clean:
	@echo "🧹 Limpiando contenedores y volúmenes..."
	docker compose -f $(COMPOSE_FILE) down -v
	docker compose -f $(COMPOSE_DEV_FILE) down -v
	@echo "✅ Limpieza completada"

# Info del entorno
info:
	@echo "🌊 Proplayas API - Información del entorno"
	@echo ""
	@echo "🔍 Entorno detectado: $(ENV)"
	@echo "📦 Contenedores esperados:"
	@echo "  - API:      $(APP_CONTAINER)"
	@echo "  - DB:       $(DB_CONTAINER)"
	@if [ "$(ENV)" = "dev" ]; then \
		echo "  - MailHog:  $(MAIL_CONTAINER)"; \
	fi
	@echo ""
	@echo "📊 Estado de contenedores Proplayas:"
	@docker ps --filter "name=proplayas" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "  No hay contenedores corriendo"
	@echo ""
	@echo "🔍 Todos los contenedores de Proplayas (incluidos detenidos):"
	@docker ps -a --filter "name=proplayas" --format "table {{.Names}}\t{{.Status}}" || echo "  No hay contenedores"
	@echo ""
	@echo "💾 Volúmenes:"
	@docker volume ls --filter "name=proplayas" --format "table {{.Name}}\t{{.Driver}}" || echo "  No hay volúmenes"

# Restart
restart:
	@echo "🔄 Reiniciando servicios ($(ENV))..."
	$(COMPOSE) restart

restart-api:
	@echo "🔄 Reiniciando API ($(APP_CONTAINER))..."
	docker restart $(APP_CONTAINER)

restart-db:
	@echo "🔄 Reiniciando PostgreSQL ($(DB_CONTAINER))..."
	docker restart $(DB_CONTAINER)

# Ejecutar comandos en la API
exec:
	@if [ -z "$(CMD)" ]; then \
		echo "⚠️  Usa: make exec CMD='comando'"; \
	else \
		docker exec -it $(APP_CONTAINER) $(CMD); \
	fi

# Backup de base de datos
backup:
	@echo "💾 Creando backup de base de datos..."
	@mkdir -p backups
	docker exec $(DB_CONTAINER) pg_dump -U proplayas proplayas_db > backups/proplayas_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup creado en backups/"

# Restaurar base de datos
restore:
	@if [ -z "$(FILE)" ]; then \
		echo "⚠️  Usa: make restore FILE=backups/proplayas_YYYYMMDD_HHMMSS.sql"; \
	else \
		echo "📥 Restaurando base de datos desde $(FILE)..."; \
		docker exec -i $(DB_CONTAINER) psql -U proplayas proplayas_db < $(FILE); \
		echo "✅ Restauración completada"; \
	fi
