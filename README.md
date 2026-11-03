# RENTIO — Backend y servicio de IA

El repositorio contiene la API principal de RENTIO (Flask), PostgreSQL y un servicio independiente de IA de marketing (FastAPI). El servicio de IA conversa con el propietario para recopilar los datos del inmueble, pregunta por los campos faltantes y genera una descripción y una referencia de canon. No implementa predicción de riesgo de inquilinos.

## Inicio local con Docker y PostgreSQL de pgAdmin

1. Copia `backend/.env.example` a `backend/.env` y `ai_service/.env.example` a `ai_service/.env`.
2. Configura en `backend/.env` las credenciales de la base PostgreSQL que ya usas desde pgAdmin. Configura `AI_INTERNAL_API_KEY` y `INTERNAL_API_KEY` con el mismo valor en ambos archivos.
3. Asegúrate de que PostgreSQL acepte conexiones desde Docker Desktop. El backend del contenedor usa `host.docker.internal` para llegar al servidor PostgreSQL de Windows.
4. Ejecuta `docker compose up --build` desde la raíz del repositorio. Compose inicia dos contenedores: la API principal en `http://localhost:5000` y el servicio de IA en `http://localhost:5001` (salud en `/health`).
5. Para detener los contenedores sin afectar la base existente, usa `docker compose down`.

PostgreSQL permanece instalado y administrado en Windows; no se crea un contenedor ni un volumen de base de datos. El frontend también se ejecuta aparte con Vite.

## Base de datos

- Script desde cero: [`backend/sql/create_database.sql`](backend/sql/create_database.sql).
- El SQL crea tablas del backend principal y el esquema `ia_marketing` para conversaciones, mensajes y resultados.
- En instalaciones nuevas ejecuta el script sobre una base vacía. Docker Compose no lo ejecuta porque usa el PostgreSQL existente.
- Para una base nueva, crea primero la base vacía en PostgreSQL y después aplica `backend/sql/create_database.sql` desde pgAdmin o, desde la raíz del repositorio, con `psql -h localhost -p 5432 -U <usuario> -d <base> -f backend/sql/create_database.sql`.
- En una base ya existente con las tablas principales, `flask db upgrade` aplica la migración del esquema de IA. Si se creó desde el script completo y se va a usar Alembic para cambios futuros, ejecuta una vez `flask --app app.py db stamp head` desde `backend`.

## API del chat

Todas las rutas públicas de IA se sirven desde el backend principal bajo `/api/v1/ia` y requieren JWT de propietario:

- `POST /conversaciones` con `propiedad_id` opcional inicia un chat y precarga datos de esa propiedad.
- `GET /conversaciones` lista los chats del propietario.
- `GET /conversaciones/<id>` recupera mensajes, datos y resultados.
- `POST /conversaciones/<id>/mensajes` con `{ "mensaje": "..." }` procesa un turno.
- `POST /conversaciones/<id>/aplicar` aplica la última descripción y precio a la propiedad asociada.

El backend valida la sesión y la propiedad. El servicio FastAPI no expone esos datos a usuarios directamente; solo acepta llamadas con `X-Internal-API-Key` desde el backend.

## Recomendación de canon

Los CSV de mercado están en `backend/data/market` y se montan en modo solo lectura dentro del servicio de IA. Los archivos comparten estadísticas de 435 barrios, por lo que el motor no suma ambas muestras. Usa medianas por barrio y alcobas cuando hay muestra suficiente y los percentiles generales disponibles para ofrecer contexto. No ajusta por área, estrato o tipo de inmueble porque los archivos no incluyen esos datos. Para referencias a nivel de ciudad sin cuartiles publicados no inventa un rango.

Los valores representan cánones solicitados en avisos, no precios de contratos cerrados. Ver [`backend/data/market/ANALISIS_DATASETS_MERCADO.md`](backend/data/market/ANALISIS_DATASETS_MERCADO.md) para cobertura, método y limitaciones.

## Ejecución y pruebas sin Docker

Backend: instala `backend/requirements.txt`, configura sus variables a partir de `backend/.env.example`, crea la base y ejecuta el SQL; inicia con `python app.py` desde `backend`.

Servicio de IA: instala `ai_service/requirements.txt`, configura `INTERNAL_API_KEY` y opcionalmente `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`; inicia con `uvicorn app.main:app --host 0.0.0.0 --port 5001` desde `ai_service`.

Las pruebas del backend usan SQLite en memoria: `pytest` desde `backend`. Las del servicio de IA: `pytest` desde `ai_service`.
