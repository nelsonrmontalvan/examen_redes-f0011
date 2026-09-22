# Examen I · IF0011 Redes de Computadoras (Sede del Caribe, Limón)

Examen interactivo de práctica con **guardado de intentos** en Supabase y **panel de reportes** para el docente.

## Archivos

| Archivo | Para quién | Uso |
|---|---|---|
| `index.html` | Estudiantes | Responder el examen (se sirve en la raíz `/`) y guardar el intento |
| `admin.html` | Docente | Reportes: quién practicó, cuántas veces y puntos por intento |
| `config.js` | Configuración | URL y anon key de Supabase |
| `schema.sql` | Docente | Crea la tabla + reglas de seguridad (se ejecuta una sola vez) |
| `tailwind.js` | Local | Habilita el examen 100% offline (sin Internet) |

## Cómo funciona

- **Estudiante:** responde → pulsa **"Revisar mi puntaje y guardar"** → ve su puntaje y sus aciertos/errores (solo los suyos) → el intento (nombre, carné, grupo, fecha, puntaje por parte y total) queda registrado en Supabase.
- **Docente:** abre `admin.html` → inicia sesión con su correo UCR y contraseña → ve el resumen por estudiante y el historial completo, y puede exportar CSV.
- **Privacidad:** los estudiantes solo **insertan** su intento; **no pueden leer** nada de nadie. Solo el docente autenticado ve los datos (política RLS en `schema.sql`).

## Configuración (una sola vez)

### 1. Crear el proyecto en Supabase
1. Entre a https://supabase.com → **Start your project** (plan Free).
2. Organización y nombre del proyecto (ej. `examen-if0011`), elija región cercana y contraseña de la base de datos.
3. Espere a que se inicialice el proyecto (~2 min).

### 2. Crear la tabla y las reglas de seguridad
1. Abra el proyecto → pestaña **SQL Editor**.
2. Copie TODO el contenido de `schema.sql`.
3. **Importante:** edite la línea `auth.jwt() ->> 'email' = 'TU_CORREO_UCR'` y ponga su correo UCR.
4. Pulse **Run**. Debe decir "Success".

### 3. Crear su usuario docente
1. Vaya a **Authentication → Users → Add user**.
2. Ponga **exactamente el mismo correo UCR** que usó en el paso 2 y una contraseña.
3. Confirme (puede crear el usuario con contraseña directamente, sin email confirm).

### 4. Copiar URL y clave anónima
1. Vaya a **Settings → API** (o Project Settings → API).
2. Copie el **Project URL** y la **anon public key**.
3. Abra `config.js` y reemplace los valores `SUSTITUIR_...`:

```js
const SUPABASE_URL = 'https://xxxx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJ...';
```

### 5. Probar
- Abra `index.html`, responda unas preguntas y pulse **"Revisar mi puntaje y guardar"**. Debe aparecer "Intento guardado".
- Abra `admin.html`, inicie sesión con su correo UCR → debe ver el intento registrado.

## Despliegue (Vercel)

Configurada la tabla y `config.js`, suba los archivos a un repositorio y desplegue como sitio estático:

```bash
git init
git add .
git commit -m "Examen IF0011 con reportes Supabase"
git branch -M main
git remote add origin https://github.com/SU_USUARIO/examen-if0011.git
git push -u origin main
```

En https://vercel.com → **Add New → Project** → importe el repositorio (framework: **Other**, sin build command). Obtendrá una URL tipo `https://examen-if0011.vercel.app` donde los estudiantes practican y usted entra a `/admin.html` para los reportes.

> En Netlify, la URL raíz `/` sirve automáticamente `index.html`; los reportes quedan en `/admin.html`.

> Nota: si al guardar un intento aparece "sin conexión", revise que `config.js` tenga las claves reales y que haya ejecutado `schema.sql`.

## Seguridad (resumen)

- Los estudiantes **no pueden leer** intentos ajenos (RLS: insert permitido, select solo docente autenticado).
- Solo el docente puede **actualizar/borrar** (revocado para anónimos en `schema.sql`).
- La clave del profesor (PIN `0101`) revela las respuestas en pantalla; se mantiene solo para revisión en clase.