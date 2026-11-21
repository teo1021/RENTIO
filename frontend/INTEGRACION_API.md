# Integración REST del frontend RENTIO

El navegador usa Fetch API contra Flask, con base `VITE_API_URL` (predeterminada `http://localhost:5000/api/v1`). Las rutas y reglas de autorización existentes se conservan; el token se envía como `Authorization: Bearer <JWT>`. El servicio FastAPI de IA es interno y nunca se llama directamente desde el navegador.

## Rutas consumidas

| Dominio | Método y ruta |
|---|---|
| Usuarios | `POST /usuarios/registro`, `POST /usuarios/login`, `GET /usuarios/perfil`, `PATCH /usuarios/perfil` |
| Administración | `GET /admin/usuarios`, `PATCH /admin/usuarios/{id}/rol` |
| Propiedades | `GET /propiedades`, `GET /propiedades/{id}`, `GET /propiedades/mis-propiedades`, `GET /propiedades/administracion`, `POST /propiedades`, `PATCH /propiedades/{id}`, `DELETE /propiedades/{id}` |
| Propiedades | `PATCH /propiedades/{id}/caracteristicas`, `POST /propiedades/{id}/imagenes`, `DELETE /propiedades/{id}/imagenes/{imagen_id}` |
| Barrios | `GET /barrios`, `POST /barrios`, `PATCH /barrios/{id}`, `GET /barrios/{id}/propiedades` |
| Características | `GET /caracteristicas`, `POST /caracteristicas` |
| Solicitudes | `POST /arriendos/solicitar`, `GET /arriendos/mis-solicitudes`, `GET /arriendos/solicitudes-recibidas`, `PATCH /arriendos/{id}/responder-visita` |
| Contratos | `POST /arriendos/{id}/generar-contrato`, `GET /arriendos/contratos`; permanece la ruta heredada `PATCH /arriendos/{id}/responder` |
| IA | `POST /ia/conversaciones`, `GET /ia/conversaciones`, `GET/PATCH /ia/conversaciones/{id}`, `POST /ia/conversaciones/{id}/mensajes` |
| IA | `POST /ia/conversaciones/{id}/crear-propiedad`, `POST /ia/conversaciones/{id}/aplicar`, `POST /ia/generar-descripcion`, `/sugerir-precio`, `/analisis-mercado`, `/mejorar-titulo`, `/extraer-datos-propiedad`, `/busqueda-texto` |

`PATCH /barrios/{id}` y `PATCH /ia/conversaciones/{id}` se añadieron para cubrir edición de barrios y persistencia de borradores. El primero conserva el ID del barrio y sus relaciones; el segundo actualiza campos permitidos en la conversación existente, sin crear filas adicionales. Ambos requieren rol propietario según corresponda (administrador para barrios y propietario para borradores).

## Roles

- Arrendatario: explorar inmuebles, enviar solicitudes, consultar sus contratos y editar su perfil.
- Propietario: administrar propiedades e imágenes, gestionar solicitudes y contratos, y registrar inmuebles asistido por IA.
- Administrador: gestionar usuarios y roles, consultar inventario y editar catálogos.

Los guards visuales de la SPA no reemplazan la autorización del backend.

## Persistencia y errores

Los mensajes enviados a IA se persisten mediante Flask; los datos editados del borrador se guardan mediante `PATCH /ia/conversaciones/{id}` con debounce. El JWT es el único dato de sesión guardado en `localStorage`; no se usa como sustituto de la persistencia del servidor.

La API de barrios solo tenía listado y creación; por eso se añadió su ruta `PATCH` sin migración de base de datos. Las fotografías de la propiedad se cargan al confirmar su creación, usando el endpoint multipart existente.

## Ejecución local

1. Inicia PostgreSQL y Flask siguiendo las instrucciones del repositorio.
2. Desde `frontend/`, ejecuta `npm install` y `npm run dev`.
3. Configura `VITE_API_URL` si Flask no está en la dirección local predeterminada.
