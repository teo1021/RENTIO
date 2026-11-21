# RENTIO Frontend

SPA construida con HTML, CSS, JavaScript nativo, Bootstrap 5 y Vite. La navegación usa History API y el navegador se comunica exclusivamente con la API Flask.

## Requisitos

- Node.js 18 o superior (20+ recomendado).
- npm.
- API Flask accesible desde el navegador.

## Desarrollo

```bash
cd frontend
npm install
npm run dev
```

La URL predeterminada es `http://localhost:3000`. Para cambiar la API, copia `.env.example` a `.env` y ajusta `VITE_API_URL`; por defecto es `http://localhost:5000/api/v1`.

## Producción

```bash
npm run build
npm run preview
```

El servidor que publique `dist/` debe devolver `index.html` para las rutas de la SPA (`/dashboard`, `/propiedades/:id`, etc.). No debe reescribir las llamadas a `/api/v1`.

## Organización

- `src/router.js`: rutas, guards de rol e historial del navegador.
- `src/api/`: cliente Fetch y servicios REST existentes.
- `src/store/auth.js`: estado de sesión; el token JWT se conserva en `localStorage`.
- `src/pages/`: pantallas independientes en JavaScript.
- `src/styles.css`: estilos propios sobre Bootstrap.

El borrador de registro con IA se guarda en PostgreSQL mediante Flask. Las fotografías elegidas para una propiedad permanecen en memoria del navegador hasta que el propietario confirma la publicación, porque la API existente solo las recibe al crear la propiedad.

## Pruebas

```bash
npm test
npm run build
```

El PDF de contrato se genera en el navegador con los datos del contrato y de su solicitud. Si faltan identificaciones, fechas, canon o inmueble, la descarga queda bloqueada. Para el rol arrendatario la API actual no entrega la identidad del propietario, por lo que no se genera un documento incompleto.
