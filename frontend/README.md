# RENTIO Frontend

Frontend independiente de RENTIO construido con React, TypeScript y Vite. Se conecta exclusivamente a la API principal Flask del proyecto; el microservicio FastAPI de IA se consume desde el backend y no se expone directamente al navegador.

## Requisitos

- Node.js 18 o superior (20+ recomendado).
- npm.
- Backend RENTIO ejecutándose y accesible desde el navegador.

## Configuración

1. Descomprime este proyecto.
2. Abre una terminal en la carpeta del frontend.
3. Instala dependencias:

   ```bash
   npm install
   ```

4. Copia `.env.example` a `.env` si necesitas configurar otra dirección de backend.
5. Verifica que `VITE_API_URL` apunte a la API Flask. Por defecto:

   ```text
   http://localhost:5000/api/v1
   ```

6. Inicia el servidor de desarrollo:

   ```bash
   npm run dev
   ```

7. Abre la URL que indique Vite (por defecto `http://localhost:3000`).

## Compilar para producción

```bash
npm run build
npm run preview
```

Consulta `INTEGRACION_API.md` para ver el mapa detallado de rutas, autenticación, permisos y límites de integración.

## Funcionalidades conectadas

- Registro e inicio de sesión con JWT (`/usuarios/registro`, `/usuarios/login`).
- Consulta y actualización del perfil (`/usuarios/perfil`).
- Propiedades: listado público, mis propiedades, creación, edición, eliminación y actualización de características.
- Solicitudes de arriendo y contratos: solicitudes enviadas/recibidas, responder solicitudes y consultar contratos.
- Administración: listado de usuarios y cambio de rol.
- Catálogos: consulta pública y creación administrativa de barrios y características.
- IA Marketing: conversaciones, mensajes, aplicación de resultados y herramientas de descripción, canon, análisis de mercado y títulos.

## Consideraciones

- El frontend no modifica el backend ni la base de datos.
- Los permisos se presentan de acuerdo con los roles reales del backend: `arrendatario`, `propietario` y `admin`.
- La API principal tiene que permitir el origen del frontend mediante CORS. El backend del ZIP original habilita CORS para `/api/*`; revisa `CORS_ALLOWED_ORIGINS` si despliegas en otro dominio.
- Algunas operaciones requieren que existan barrios y características en sus catálogos.
- El registro público permite crear cuentas de tipo `arrendatario` o `propietario`; la cuenta `admin` debe asignarse por el mecanismo administrativo del backend.
- No existe endpoint de carga de imágenes en el backend original, por lo que esta versión no inventa una carga de archivos. Las tarjetas muestran un tratamiento visual genérico hasta que exista un endpoint de imágenes.
- Las respuestas de IA y los análisis de mercado dependen de la configuración y disponibilidad del microservicio interno.
