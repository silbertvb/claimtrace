# Cómo usar ClaimTrace

(Bloque 2): el stack levanta `db` (Postgres + pgvector) 
y `api` (FastAPI con `/health`). `n8n` se añadirá en el Bloque 8.

## Requisitos
- Docker Desktop en marcha.

## Cómo levantarlo

1. Copia la plantilla de variables y cambia la contraseña:
   ```powershell
   Copy-Item .env.example .env
   ```
   (En Linux o macOS: `cp .env.example .env`). Edita `.env` y sustituye
    `POSTGRES_PASSWORD`. `N8N_ENCRYPTION_KEY` solo hará falta cuando se añada n8n.
   
2. Construye y arranca:
   ```powershell
   docker compose up -d --build
   ```
3. Comprueba el estado; `claimtrace-db` debe salir `healthy`:
   ```powershell
   docker compose ps
   ```
4. Comprueba que la API llega a la base:
   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/health
   ```
   (En Linux o macOS: `curl http://127.0.0.1:8000/health`). Debe devolver `status: ok` y `db: ok`.
   Con el stack en marcha, la API está en `http://127.0.0.1:8000` 
   y Postgres en `127.0.0.1:5433` (puerto `POSTGRES_HOST_PORT`). Ambos solo son accesibles desde tu máquina.

Para pararlo: `docker compose down`. Con `docker compose down -v` se borran también los datos de la base.

## Desarrollo local (opcional)

La API se ejecuta siempre en Docker. El entorno virtual solo sirve para que el
editor reconozca las dependencias (autocompletado y avisos de VS Code). El
contenedor usa Python 3.12; para el editor basta con una versión reciente de
Python en tu equipo, no hace falta que coincida. Si la instalación falla con tu
versión, prueba con una más cercana a la 3.12.

1. Crea el entorno e instala las mismas dependencias que usa la imagen:
   ```powershell
      python -m venv .venv
      .\.venv\Scripts\python.exe -m pip install -r services\api\requirements.txt
   ```
   (En Linux o macOS: `python3 -m venv .venv` y
   `.venv/bin/python -m pip install -r services/api/requirements.txt`).

2. En VS Code: `Ctrl + Shift + P`, **Python: Select Interpreter** y elige el de `.venv`.

Si cambias `services/api/requirements.txt`, repite el `pip install` y
reconstruye la imagen con `docker compose up -d --build api`, para que el editor
y el contenedor usen las mismas versiones.

## Problemas frecuentes

- **`ports are not available` en el 5433:** hay otro Postgres usando ese puerto. 
  Cambia `POSTGRES_HOST_PORT` en `.env` (por ejemplo a 5434). El
  puerto interno `POSTGRES_PORT` no se toca.
- **`/health` da "conexión terminada" nada más arrancar:** la API aún no estaba
  escuchando. Espera unos segundos y repite.
- **`docker compose` no se reconoce:** Docker Desktop no está en marcha o el
  motor no ha terminado de arrancar. Comprueba con `docker version`.
- **La extensión `vector` no aparece:** el script de arranque solo se ejecuta
  cuando el volumen está vacío. Si el volumen ya existía, ejecuta
  `docker compose down -v` y vuelve a arrancar.
- **Error `POSTGRES_PASSWORD ... missing a value` al arrancar:** falta el
  archivo `.env` o la contraseña está vacía. Copia `.env.example` a `.env` y
  rellena `POSTGRES_PASSWORD`.
```