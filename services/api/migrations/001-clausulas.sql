-- 001-clausulas.sql
-- Tabla de clausulas indexadas (ADR-004, D3).
-- No incluir BEGIN/COMMIT/ROLLBACK: el ejecutor ya abre la transaccion
-- y un COMMIT aqui rompe la atomicidad con la fila de "migrations".

CREATE TABLE clausulas (
    id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id      text        NOT NULL UNIQUE,
    titulo         text        NOT NULL,
    texto          text        NOT NULL,
    metadatos      jsonb       NOT NULL,
    hash_contenido text        NOT NULL,
    embedding      vector(1536) NOT NULL,
    modelo         text        NOT NULL,
    dimensiones    integer     NOT NULL,
    indexada_en    timestamptz NOT NULL
);