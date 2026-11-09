# RENTIO — Asistente IA, backend y servicio de IA

RENTIO ofrece un único Asistente IA con dos modos: registro de propiedades mediante conversación y marketing para inmuebles existentes. El backend Flask guarda las conversaciones y propiedades; el servicio independiente FastAPI extrae los datos, solicita los faltantes y reutiliza los generadores de contenido y las referencias de canon.

## Inicio local con Docker

1. Copia `.env.example` a `.env` y reemplaza los valores de desarrollo antes de compartir o desplegar el proyecto.
2. Ejecuta `docker compose up --build` desde la raíz del repositorio.
3. Compose inicia PostgreSQL primero, espera la disponibilidad de la base y del servicio de IA, y luego inicia Flask. La API queda en `http://localhost:5000`, el servicio de IA en `http://localhost:5001` y su salud en `http://localhost:5001/health`.
4. Las fotografías se guardan en el volumen persistente `rentio_uploads`. Para detener los contenedores conserva los datos con `docker compose down`; `docker compose down -v` elimina también los volúmenes.

El script de inicialización solo se ejecuta cuando PostgreSQL crea un volumen nuevo. Si cambias el SQL, para recrear la base local elimina el volumen con `docker compose down -v` y vuelve a iniciar el stack.

## Base de datos

- Script desde cero: [`backend/sql/create_database.sql`](backend/sql/create_database.sql).
- El SQL crea tablas del backend principal y el esquema `ia_marketing` para conversaciones, mensajes y resultados.
- En instalaciones nuevas ejecuta el script sobre una base vacía. Con Docker Compose se ejecuta automáticamente.
- Sin Docker, crea primero la base vacía con `python scripts/create_db.py` desde `backend` y después aplica `psql -h localhost -p 5433 -U <usuario> -d <base> -f sql/create_database.sql`.
- En una base ya existente con las tablas principales, `flask db upgrade` aplica la migración del esquema de IA. Si se creó desde el script completo y se va a usar Alembic para cambios futuros, ejecuta una vez `flask --app app.py db stamp head` desde `backend`.

## API del chat

Todas las rutas públicas de IA se sirven desde el backend principal bajo `/api/v1/ia` y requieren JWT de propietario:

- `POST /conversaciones` con `propiedad_id` opcional inicia un chat y precarga datos de esa propiedad.
- `GET /conversaciones` lista los chats del propietario.
- `GET /conversaciones/<id>` recupera mensajes, datos y resultados.
- `POST /conversaciones/<id>/mensajes` con `{ "mensaje": "..." }` procesa un turno.
- `POST /conversaciones/<id>/aplicar` aplica la última descripción y precio a la propiedad asociada.

El backend valida la sesión y la propiedad. El servicio FastAPI no expone esos datos a usuarios directamente; solo acepta llamadas con `X-Internal-API-Key` desde el backend. El registro confirma y crea la propiedad junto con sus fotografías en una sola operación, y no reutiliza el canon sugerido como si lo hubiera indicado el propietario.

## Modo de desarrollo local en PowerShell

Se necesitan cuatro servicios/procesos: PostgreSQL en el puerto `5433`, FastAPI en `5001`, Flask en `5000` y Vite en `3000` (si está ocupado, Vite elige otro puerto disponible). Docker Compose inicia PostgreSQL, FastAPI y Flask; el frontend se inicia por separado.

La opción recomendada es Docker Compose: desde la raíz, ejecuta `Copy-Item .env.example .env` (solo la primera vez), revisa las variables y luego `docker compose up --build`. El Compose comparte la llave interna entre Flask y FastAPI.

Para ejecutar los procesos por separado:

1. Inicia PostgreSQL y prepara la base descrita en la sección **Base de datos**. Configura `backend/.env` a partir de `backend/.env.example`; usa el mismo valor local en `AI_INTERNAL_API_KEY`.
2. En una terminal, inicia el servicio de IA:

   ```powershell
   Set-Location ai_service
   ..\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 5001
   ```

   Si aún no existe `backend/.venv`, crea un entorno e instala `backend/requirements-dev.txt` y `ai_service/requirements.txt` según corresponda. El servicio lee `backend/.env` en desarrollo y acepta allí `AI_INTERNAL_API_KEY`; también puede configurarse directamente como `INTERNAL_API_KEY`.

3. En otra terminal, inicia Flask:

   ```powershell
   Set-Location backend
   .\.venv\Scripts\python.exe app.py
   ```

4. En una tercera terminal, inicia el frontend:

   ```powershell
   Set-Location frontend
   npm run dev
   ```

El backend usa `AI_SERVICE_URL=http://localhost:5001` cuando se ejecuta fuera de Docker; dentro de Compose usa el nombre de servicio `http://ai-service:5001`. Si FastAPI no está escuchando o la llave compartida no coincide, el chat muestra un error explícito `503` (disponibilidad/configuración); los tiempos agotados se reportan como `504`. No se guarda ningún mensaje como procesado cuando el servicio falla.

## Recomendación de canon

Los CSV de mercado están en `backend/data/market` y se montan en modo solo lectura dentro del servicio de IA. Los archivos comparten estadísticas de 435 barrios, por lo que el motor no suma ambas muestras. Usa medianas por barrio y alcobas cuando hay muestra suficiente y los percentiles generales disponibles para ofrecer contexto. No ajusta por área, estrato o tipo de inmueble porque los archivos no incluyen esos datos. Para referencias a nivel de ciudad sin cuartiles publicados no inventa un rango.

Los valores representan cánones solicitados en avisos, no precios de contratos cerrados. Ver [`backend/data/market/ANALISIS_DATASETS_MERCADO.md`](backend/data/market/ANALISIS_DATASETS_MERCADO.md) para cobertura, método y limitaciones.

## Ejecución y pruebas sin Docker

Backend: instala `backend/requirements-dev.txt`, configura sus variables a partir de `backend/.env.example`, crea la base y ejecuta el SQL; inicia con `python app.py` desde `backend`.

Servicio de IA: instala `ai_service/requirements.txt`, configura una llave compartida (`INTERNAL_API_KEY` o `AI_INTERNAL_API_KEY`) y opcionalmente `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`; inicia con `uvicorn app.main:app --host 0.0.0.0 --port 5001` desde `ai_service`.

Las pruebas del backend usan SQLite en memoria: `pytest` desde `backend`. Las del servicio de IA: `pytest` desde `ai_service`.
