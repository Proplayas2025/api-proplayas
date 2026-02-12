-- Migración para cambiar columnas DateTime de timezone-aware a naive (sin zona horaria)
-- Esto asegura que las fechas se guarden exactamente como se ingresan, sin conversiones UTC

-- Tabla: content
ALTER TABLE content 
    ALTER COLUMN event_date TYPE TIMESTAMP WITHOUT TIME ZONE,
    ALTER COLUMN publication_date TYPE TIMESTAMP WITHOUT TIME ZONE,
    ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE,
    ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE;

-- Tabla: invitations
ALTER TABLE invitations 
    ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE,
    ALTER COLUMN expires_at TYPE TIMESTAMP WITHOUT TIME ZONE;

-- Nota: Esta migración cambia las columnas pero mantiene los valores existentes
-- Las fechas existentes se mantendrán en su representación actual
