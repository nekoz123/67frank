# Zona Leonida — canal de GTA 6 listo para el lanzamiento

10 vídeos terminados (1080p, 30 fps, voz en español, música original, subtítulos) + miniaturas + fichas de subida + kit de canal.

## Qué hay en cada carpeta

| Carpeta | Contenido |
|---|---|
| `videos/` | Por cada vídeo: `.mp4` (el vídeo), `_miniatura.jpg` (1280×720), `.srt` (subtítulos en español), `_ficha.txt` (título, descripción con capítulos y etiquetas para copiar y pegar) |
| `canal/` | `banner_2560x1440.jpg`, `avatar_800x800.png`, `marca_de_agua_150x150.png` |
| `scripts.py` | Los 10 guiones (texto y escenas). Si cambias una frase, vuelves a generar el vídeo |
| `engine/` | Motor que genera voz, animaciones, música y montaje |

## Los 10 vídeos (en orden de prioridad)

| # | Vídeo | Qué búsqueda ataca |
|---|---|---|
| 01 | ¿A qué hora sale GTA 6? Hora exacta en tu país | "a qué hora sale GTA 6", "GTA 6 hora México/España" |
| 02 | Precarga: cuánto pesa (212 GB) y cómo descargarlo antes | "GTA 6 cuánto pesa", "GTA 6 precarga" |
| 03 | Standard vs Ultimate: ¿cuál comprar? | "GTA 6 precio", "GTA 6 ediciones", "Ultimate Edition" |
| 04 | ¿GTA 6 en PC, PS4 o Xbox One? | "GTA 6 PC", "GTA 6 PS4" |
| 05 | El mapa explicado: Leonida región por región | "mapa GTA 6", "Leonida", "Vice City" |
| 06 | Lucia y Jason: todos los personajes | "personajes GTA 6", "Lucia GTA 6", "Jason GTA 6" |
| 07 | Los 3 tráilers en 4 minutos | "GTA 6 trailer", "GTA 6 trailer 3" |
| 08 | GTA 6 vs GTA 5: 8 diferencias | "GTA 6 vs GTA 5" |
| 09 | 10 consejos antes de jugar (y estafas) | "GTA 6 consejos", "GTA 6 PC gratis" (estafas) |
| 10 | GTA 6 en números: el lanzamiento más grande | "GTA 6 récords", "GTA 6 ventas" |

## Calendario de subida recomendado

GTA 6 se desbloquea a **medianoche local del jueves 19 de noviembre**. Por eso los vídeos 01 y 02 pierden casi todo su valor si salen el jueves por la mañana: la gente los busca **antes** de medianoche.

**Mi recomendación (hora de España / CDMX es 7 h menos):**

| Cuándo | Vídeo |
|---|---|
| **Mié 18, lo antes posible** | 01 hora de salida · 02 precarga |
| Jue 19, 10:00 | 09 consejos y estafas |
| Jue 19, 12:00 | 05 mapa |
| Jue 19, 14:00 | 06 personajes |
| Jue 19, 16:00 | 03 ediciones |
| Jue 19, 18:00 | 04 PC / PS4 |
| Jue 19, 20:00 | 08 GTA 6 vs GTA 5 |
| Vie 20, 12:00 | 07 tráilers |
| Vie 20, 18:00 | 10 números y récords (invita a predecir ventas → comentarios) |

Si prefieres subir todo el jueves, súbelo **hoy** como "Programado" en YouTube Studio con esas horas y así no tienes que estar pendiente.

## Cómo subir cada vídeo (5 minutos por vídeo)

1. YouTube Studio → **Crear → Subir vídeo** → elige `videos/XX_....mp4`.
2. Abre `videos/XX_..._ficha.txt` y copia **título**, **descripción** y **etiquetas**.
3. **Miniatura** → sube `XX_..._miniatura.jpg`.
4. **¿Es contenido creado para niños?** → No.
5. **Contenido alterado o sintético** → la narración es una voz generada por IA. Revisa la política actual de YouTube; ante la duda, márcalo como **Sí** (no penaliza y evita problemas).
6. **Subtítulos** → Añadir → Subir archivo → `XX_....srt` (Español).
7. **Elementos finales** → añade "Suscribirse" + "Vídeo recomendado" en los últimos 10–15 s (la pantalla final de cada vídeo deja hueco para eso).
8. Visibilidad → **Programar** con la fecha del calendario.

Configura el canal una sola vez: nombre **Zona Leonida** (o el que quieras), sube `canal/avatar_800x800.png`, `canal/banner_2560x1440.jpg` y en Personalización → Marca la `marca_de_agua_150x150.png`.

## Avisos importantes

- **Derechos de autor:** no se usa ni una imagen, logo, clip ni música de Rockstar. Todo (fondos, mapa, siluetas, música) está generado desde cero, así que no deberías recibir reclamaciones de Content ID. El mapa y las siluetas se presentan como **ilustrativos**.
- **Datos:** todo sale de anuncios oficiales y medios a 17/11/2026. Donde las fuentes no coinciden (horas en EE. UU., tamaño exacto por consola, extras de la Ultimate) el guion lo dice. Si el parche del día uno cambia algo, edita `scripts.py` y vuelve a generar ese vídeo.
- **No inventé nada del gameplay** (trucos, dinero, misiones) porque nadie lo ha jugado todavía. Eso es lo siguiente: en cuanto salga el juego, la gente buscará trucos, cómo ganar dinero, mejores coches, etc. Esos vídeos hay que hacerlos jugando.

## Volver a generar un vídeo

```bash
cd engine
python3 build.py 03_standard_vs_ultimate     # un vídeo
./render_all.sh                               # los 10
python3 make_meta.py                          # fichas + kit de canal
```

Requisitos: `ffmpeg`, Python con `pillow numpy soundfile kokoro-onnx`, y los modelos de voz en `engine/models/` (`kokoro-v1.0.onnx` → renombrar a `kokoro.onnx`, y `voices-v1.0.bin` → `voices.bin`, del repositorio thewh1teagle/kokoro-onnx).
