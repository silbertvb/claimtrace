"""Ejecutor de migraciones SQL (ADR-004, D3).

Aplica en orden las migraciones de `migrations/` que aun no estan registradas
en la tabla `migrations`, cada una en su propia transaccion junto con su fila
de registro. Se puede lanzar con `python -m app.core.migrations` o llamando a
`aplicar_migraciones()` desde el `lifespan` de la API.

Reglas para los archivos .sql:
- Nombre `NNN-descripcion.sql` (tres digitos).
- NO incluir BEGIN, COMMIT ni ROLLBACK: el ejecutor ya abre la transaccion y un
  COMMIT dentro del archivo rompe la atomicidad con el registro (comprobado el
  29 oct). No hay comprobacion automatica (ADR-004, D3; decision P4).
- Una migracion ya aplicada no se edita: su checksum haria fallar el arranque.
"""
import hashlib
import logging
import re
from pathlib import Path

from app.core.db import _conectar

log = logging.getLogger(__name__)

# Clave del bloqueo de sesion (pg_advisory_lock). Convencion "bloque + numero":
# bloque 4, lock 1. Si hiciera falta otro lock, seguir el patron (40002, 50001...)
# para no repetir claves. Postgres no comprueba esta convencion.
CLAVE_LOCK_MIGRACIONES = 40001

# En el contenedor: /app/app/core/migrations.py -> /app/migrations.
# En el repo: services/api/app/core/migrations.py -> services/api/migrations.
CARPETA = Path(__file__).resolve().parent.parent.parent / "migrations"

# Patron del nombre de una migracion: tres digitos, guion, descripcion y ".sql"
# (por ejemplo "001-clausulas.sql"). Los tres primeros digitos son la version.
# Un archivo que no lo cumpla (como "01-x.sql" o "001_x.sql") hace fallar el
# arranque antes de tocar la base.
_PATRON_NOMBRE = re.compile(r"^(\d{3})-.+\.sql$")


class ErrorMigracion(Exception):
    """Fallo al aplicar o verificar migraciones; la API no debe arrancar."""


def _leer(ruta: Path) -> tuple[str, str]:
    """Devuelve (contenido, checksum) con los saltos de linea normalizados a LF."""
    datos = ruta.read_bytes().replace(b"\r\n", b"\n")
    return datos.decode("utf-8"), hashlib.sha256(datos).hexdigest()


def aplicar_migraciones() -> list[str]:
    """Aplica las migraciones pendientes y devuelve las versiones aplicadas."""
    archivos = sorted(CARPETA.glob("*.sql"))
    for archivo in archivos:
        if not _PATRON_NOMBRE.match(archivo.name):
            raise ErrorMigracion(f"Nombre de migracion no valido: {archivo.name}")

    aplicadas: list[str] = []
    # autocommit=True: el bloqueo y la tabla de registro se confirman solos, y
    # cada migracion corre en la transaccion que abre conn.transaction()
    # (decision P1). El finally cierra la conexion siempre, y cerrarla es lo
    # que libera el bloqueo de sesion.
    conn = _conectar(autocommit=True)
    try:
        conn.execute("SELECT pg_advisory_lock(%s)", (CLAVE_LOCK_MIGRACIONES,))
        conn.execute(
            "CREATE TABLE IF NOT EXISTS migrations ("
            "version text PRIMARY KEY, "
            "nombre text NOT NULL, "
            "checksum text NOT NULL, "
            "aplicada_en timestamptz NOT NULL)"
        )
        for archivo in archivos:
            version = archivo.name[:3]
            contenido, checksum = _leer(archivo)
            fila = conn.execute(
                "SELECT checksum FROM migrations WHERE version = %s", (version,)
            ).fetchone()
            if fila is not None:
                if fila[0] != checksum:
                    raise ErrorMigracion(
                        f"La migracion {archivo.name} ya aplicada ha cambiado: "
                        f"checksum guardado {fila[0]}, calculado {checksum}"
                    )
                continue
            with conn.transaction():
                conn.execute(contenido)
                conn.execute(
                    "INSERT INTO migrations (version, nombre, checksum, aplicada_en) "
                    "VALUES (%s, %s, %s, now())",
                    (version, archivo.name, checksum),
                )
            aplicadas.append(version)
            log.info("Migracion %s aplicada", archivo.name)
    finally:
        conn.close()  # cerrar la conexion libera el lock (comprobado el 29 oct)
    return aplicadas


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    resultado = aplicar_migraciones()
    print(f"Migraciones aplicadas: {resultado or 'ninguna'}")