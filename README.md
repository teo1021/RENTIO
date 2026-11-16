# RENTIO — Asistente IA, backend y servicio de IA

RENTIO ofrece un único Asistente IA con dos modos: registro de propiedades mediante conversación y marketing para inmuebles existentes. El backend Flask guarda las conversaciones y propiedades; el servicio independiente FastAPI extrae los datos, solicita los faltantes y reutiliza los generadores de contenido y las referencias de canon.

## PostgreSQL local con Docker

1. Copia `.env.example` a `.env` y reemplaza los valores de desarrollo antes de compartir o desplegar el proyecto.
2. Ejecuta `docker compose up -d postgres` desde la raíz del repositorio. El Compose actual inicia únicamente PostgreSQL y lo publica en `localhost:5433`.
3. La primera inicialización crea el volumen y ejecuta el SQL de catálogo. Los cambios posteriores a esos SQL no se vuelven a ejecutar sobre un volumen existente.
4. Para detener PostgreSQL sin borrar los datos usa `docker compose down`. No uses `docker compose down -v` salvo que quieras eliminar deliberadamente la base local completa.

El script de inicialización solo se ejecuta cuando PostgreSQL crea un volumen nuevo. Para probar cambios de bootstrap, usa una base/volumen de prueba aislado; no elimines volúmenes con datos existentes.

## Base de datos

- Script desde cero: [`backend/sql/create_database.sql`](backend/sql/create_database.sql).
- El SQL crea tablas del backend principal y el esquema `ia_marketing` para conversaciones, mensajes y resultados.
- En instalaciones nuevas ejecuta el script sobre una base vacía. Con Docker Compose se ejecuta automáticamente.
- Sin Docker, crea primero la base vacía con `python scripts/create_db.py` desde `backend` y después aplica `psql -h localhost -p 5433 -U <usuario> -d <base> -f sql/create_database.sql`.
- En una base ya existente con las tablas principales, ejecuta desde `backend` `.\.venv\Scripts\python.exe -m flask --app app:crear_app db upgrade` para aplicar las migraciones pendientes, incluida la reconciliación aditiva del esquema. Si se creó desde el script completo y se va a usar Alembic para cambios futuros, ejecuta una vez `.\.venv\Scripts\python.exe -m flask --app app:crear_app db stamp head`.

## Administración de usuarios

El rol `admin` no se puede elegir en el registro ni asignar desde la pantalla o API de cambio de rol. Para crear la primera cuenta administradora, registra primero una cuenta normal con el correo autorizado y su propia contraseña; luego, desde `backend`, ejecuta:

```powershell
.\.venv\Scripts\python.exe scripts\promover_admin.py admin@tu-dominio.example --confirmar
```

El comando usa la configuración de base de datos ya instalada y no contiene una contraseña predeterminada. El usuario inicia sesión desde `/login` con las credenciales de la cuenta creada. La promoción y democión de cuentas administrativas requiere acceso controlado al proceso local y a la base de datos.

## API del chat

Todas las rutas públicas de IA se sirven desde el backend principal bajo `/api/v1/ia` y requieren JWT de propietario:

- `POST /conversaciones` con `propiedad_id` opcional inicia un chat y precarga datos de esa propiedad.
- `GET /conversaciones` lista los chats del propietario.
- `GET /conversaciones/<id>` recupera mensajes, datos y resultados.
- `POST /conversaciones/<id>/mensajes` con `{ "mensaje": "..." }` procesa un turno.
- `POST /conversaciones/<id>/aplicar` aplica la última descripción y precio a la propiedad asociada.

El backend valida la sesión y la propiedad. El servicio FastAPI no expone esos datos a usuarios directamente; solo acepta llamadas con `X-Internal-API-Key` desde el backend. El registro confirma y crea la propiedad junto con sus fotografías en una sola operación, y no reutiliza el canon sugerido como si lo hubiera indicado el propietario.

## Modo de desarrollo local en PowerShell

Se necesitan cuatro servicios/procesos: PostgreSQL en el puerto `5433`, FastAPI en `5001`, Flask en `5000` y Vite en `3000` (si está ocupado, Vite elige otro puerto disponible).

Desde la raíz, inicia PostgreSQL con `docker compose up -d postgres`. El archivo Compose no inicia Flask, FastAPI ni Vite; inicia cada aplicación por separado como se indica abajo.

Para ejecutar los procesos por separado:

1. Inicia PostgreSQL y prepara la base descrita en la sección **Base de datos**. Configura `backend/.env` a partir de `backend/.env.example`; al usar Compose, mantén `DB_USER`, `DB_PASSWORD` y `DB_NAME` iguales a los de la raíz `.env`. Usa el mismo valor local en `AI_INTERNAL_API_KEY` para Flask y FastAPI.
2. En una terminal, inicia el servicio de IA:

   ```powershell
   Set-Location ai_service
   ..\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 5001
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

El backend usa `AI_SERVICE_URL=http://localhost:5001` para el inicio local descrito aquí. Si FastAPI no está escuchando o la llave compartida no coincide, el chat muestra un error explícito `503` (disponibilidad/configuración); los tiempos agotados se reportan como `504`. No se guarda ningún mensaje como procesado cuando el servicio falla.

## Recomendación de canon

Los CSV de mercado están en `backend/data/market` y se montan en modo solo lectura dentro del servicio de IA. Los archivos comparten estadísticas de 435 barrios, por lo que el motor no suma ambas muestras. Usa medianas por barrio y alcobas cuando hay muestra suficiente y los percentiles generales disponibles para ofrecer contexto. No ajusta por área, estrato o tipo de inmueble porque los archivos no incluyen esos datos. Para referencias a nivel de ciudad sin cuartiles publicados no inventa un rango.

Los valores representan cánones solicitados en avisos, no precios de contratos cerrados. Ver [`backend/data/market/ANALISIS_DATASETS_MERCADO.md`](backend/data/market/ANALISIS_DATASETS_MERCADO.md) para cobertura, método y limitaciones.

## Ejecución y pruebas sin Docker

Backend: instala `backend/requirements-dev.txt`, configura sus variables a partir de `backend/.env.example`, crea la base y ejecuta el SQL; inicia con `python app.py` desde `backend`.

Servicio de IA: instala `ai_service/requirements.txt`, configura una llave compartida (`INTERNAL_API_KEY` o `AI_INTERNAL_API_KEY`) y opcionalmente `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`; inicia con `uvicorn app.main:app --host 127.0.0.1 --port 5001` desde `ai_service`.

Las pruebas del backend usan SQLite en memoria: `pytest` desde `backend`. Las del servicio de IA: `pytest` desde `ai_service`.
