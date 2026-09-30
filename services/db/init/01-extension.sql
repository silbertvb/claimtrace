-- Activa pgvector la primera vez que se crea la base de datos.
-- Postgres ejecuta los .sql de esta carpeta solo si el volumen está vacío.
CREATE EXTENSION IF NOT EXISTS vector;