# Examen I · IF0011 Redes de Computadoras (Sede del Caribe, Limón)

Examen interactivo de práctica con **guardado de intentos** en Supabase y **panel de reportes** para el docente.

## Archivos

| Archivo | Para quién | Uso |
|---|---|---|
| `index.html` | Estudiantes | Responder el examen (se sirve en la raíz `/`) y guardar el intento |
| `admin.html` | Docente | Reportes: quién practicó, cuántas veces, puntos por intento **y las respuestas que escribió cada uno** |
| `config.js` | Configuración | URL y anon key de Supabase |
| `schema.sql` | Docente | Crea la tabla + reglas de seguridad (se puede volver a pegar: es idempotente) |
| `tailwind.js` | Local | Habilita el examen 100% offline (sin Internet) |

## Cómo funciona

- **Estudiante:** responde → pulsa **"Revisar mi puntaje y guardar"** → ve la **nota desglosada** (puntos, % y
  nota final 0–100, parte por parte) → puede **descargar su retroalimentación** (`retroalimentacion-<carnet>.html`):
  indica cuántas buenas/malas tiene por parte y explica cada incorrecta con su respuesta, la correcta y el porqué
  (teoría, subnetting y prácticos) → el intento (nombre, carné, grupo, fecha, puntos por parte, total **y todas
  las respuestas que escribió**) queda registrado en Supabase.
- **Docente:** abre `admin.html` → inicia sesión con su correo UCR y contraseña → ve el resumen por estudiante y el
  historial completo, y en el **detalle** de cada estudiante puede desplegar **"Ver"** por intento para leer las
  respuestas crudas: las incorrectas de la Parte I con su justificación, y **todo lo que el estudiante escribió** en
  Parte II y III junto con la respuesta esperada (marcado ✓/✗). También puede exportar CSV.
- **Orden aleatorio:** cada vez que se abre el examen se barajan las preguntas de cada semana, las opciones de
  respuesta de cada pregunta, los 7 ítems de subnetting y los 3 casos prácticos. El puntaje y la clave no cambian.
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

> **Tabla ya creada en una versión anterior:** vuelva a pegar TODO `schema.sql` y ejecútelo otra vez; agrega la
> columna `respuestas` por sí solo. O ejecute solo esto en el SQL Editor:
>
> ```sql
> alter table public.intentos add column if not exists respuestas jsonb;
> ```
>
> Si la columna falta, el examen **igual guarda el puntaje** (solo muestra un aviso pidiendo aplicar el UPDATE).

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
- Abra `admin.html`, inicie sesión con su correo UCR → debe ver el intento registrado → en **Detalle del estudiante**,
  en la fila del intento, pulse **Ver** para leer las respuestas que escribió.

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
- Parte II: la **división de bloques** del SVG de subnetting está oculta; se revela con la clave del docente (`1977`).
  Al tercer intento fallido la clave queda **bloqueada** en ese navegador (persiste al recargar); el PIN `0101`
  desbloquea y revela de todos modos.
- Ambas claves están en el código fuente de `index.html`: quien abra "ver código fuente" puede leerlas. Si el
  examen se usa como prueba formal, considere publicar solo la versión sin claves.