# Integración del frontend RENTIO con el backend existente

Este proyecto contiene únicamente el frontend. No incluye ni reemplaza el backend, el microservicio de IA o la base de datos.

## API principal

- Tecnología: Flask.
- URL local: `http://localhost:5000`.
- Prefijo: `/api/v1`.
- Variable configurable: `VITE_API_URL`.
- Valor predeterminado: `http://localhost:5000/api/v1`.

El navegador se comunica únicamente con Flask. El microservicio FastAPI de IA continúa siendo interno y Flask lo invoca mediante su cliente configurado en el servidor.

## Autenticación

El inicio de sesión envía `correo` y `contrasena` a `POST /usuarios/login`. El frontend recibe `data.token` y `data.usuario`, guarda el JWT localmente y lo envía como `Authorization: Bearer <token>` en las solicitudes protegidas. Al recargar la aplicación valida la sesión con `GET /usuarios/perfil`.

El registro utiliza `POST /usuarios/registro` y solo permite los roles públicos `arrendatario` y `propietario`. El rol `admin` debe asignarse mediante el mecanismo administrativo del backend.

## Rutas integradas

| Módulo | Método y ruta | Uso desde el frontend |
|---|---|---|
| Usuarios | `POST /usuarios/registro` | Crear cuenta |
| Usuarios | `POST /usuarios/login` | Iniciar sesión |
| Usuarios | `GET /usuarios/perfil` | Consultar perfil |
| Usuarios | `PATCH /usuarios/perfil` | Actualizar perfil |
| Administración | `GET /admin/usuarios` | Listar cuentas (admin) |
| Administración | `PATCH /admin/usuarios/{id}/rol` | Cambiar rol (admin) |
| Propiedades | `GET /propiedades` | Consultar inventario público |
| Propiedades | `GET /propiedades/{id}` | Consultar detalle |
| Propiedades | `GET /propiedades/mis-propiedades` | Consultar inmuebles propios (propietario) |
| Propiedades | `POST /propiedades` | Crear inmueble (propietario) |
| Propiedades | `PATCH /propiedades/{id}` | Editar inmueble (propietario/admin según permisos del backend) |
| Propiedades | `DELETE /propiedades/{id}` | Eliminar inmueble (propietario/admin según permisos del backend) |
| Propiedades | `PATCH /propiedades/{id}/caracteristicas` | Actualizar amenidades |
| Barrios | `GET /barrios` | Consultar catálogo |
| Barrios | `POST /barrios` | Crear barrio (admin) |
| Barrios | `GET /barrios/{id}/propiedades` | Endpoint disponible en backend; no se necesita para el flujo principal actual |
| Características | `GET /caracteristicas` | Consultar catálogo |
| Características | `POST /caracteristicas` | Crear característica (admin) |
| Arriendos | `POST /arriendos/solicitar` | Enviar solicitud |
| Arriendos | `GET /arriendos/mis-solicitudes` | Consultar solicitudes enviadas |
| Arriendos | `GET /arriendos/solicitudes-recibidas` | Consultar solicitudes recibidas (propietario) |
| Arriendos | `PATCH /arriendos/{id}/responder` | Aceptar/rechazar solicitud y formalizar contrato según reglas del backend |
| Arriendos | `GET /arriendos/contratos` | Consultar contratos del usuario |
| IA Marketing | `POST /ia/conversaciones` | Crear conversación opcionalmente asociada a propiedad |
| IA Marketing | `GET /ia/conversaciones` | Listar conversaciones |
| IA Marketing | `GET /ia/conversaciones/{id}` | Consultar conversación, mensajes y resultados |
| IA Marketing | `POST /ia/conversaciones/{id}/mensajes` | Enviar turno al asistente |
| IA Marketing | `POST /ia/conversaciones/{id}/aplicar` | Aplicar resultado a propiedad asociada |
| IA Marketing | `POST /ia/generar-descripcion` | Generar descripción |
| IA Marketing | `POST /ia/sugerir-precio` | Estimar canon |
| IA Marketing | `POST /ia/analisis-mercado` | Consultar análisis de mercado |
| IA Marketing | `POST /ia/mejorar-titulo` | Proponer títulos |

Todas las rutas anteriores se envían con el prefijo `/api/v1` configurado en la URL base.

## Permisos representados en la interfaz

- **Arrendatario:** explora inmuebles disponibles, envía solicitudes, consulta sus solicitudes y contratos, y actualiza su perfil.
- **Propietario:** gestiona sus propiedades, atiende solicitudes recibidas, consulta contratos y utiliza Marketing IA.
- **Administrador:** consulta y gestiona usuarios, roles, catálogos e inventario de propiedades.

La autorización real sigue estando en los decoradores y servicios del backend. Las restricciones visuales no sustituyen las validaciones del servidor.

## Ejecución local

1. Inicia PostgreSQL y el backend Flask según las instrucciones del repositorio original.
2. Desde esta carpeta instala dependencias con `npm install`.
3. Copia `.env.example` como `.env` si necesitas cambiar la dirección del backend.
4. Ejecuta `npm run dev` y abre `http://localhost:3000`.

El backend original configura CORS para las rutas `/api/*`. Si despliegas el frontend en otro dominio, configura `CORS_ALLOWED_ORIGINS` en el entorno del servidor.

## Límites que dependen del backend

- El backend original no expone una ruta de carga/gestión de imágenes. El frontend muestra las URLs que ya vengan en `imagenes`, pero no inventa una carga de archivos.
- El chat y las herramientas de Marketing IA dependen de que el backend Flask y su microservicio interno estén configurados y disponibles.
- Los indicadores del dashboard se calculan con respuestas disponibles. No se inventan métricas que el backend no exponga.
