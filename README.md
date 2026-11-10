 JKaudio

Aplicación web para generar audio a partir de texto mediante inteligencia artificial. Utiliza Django como backend, Kokoro TTS para la síntesis de voz y Redis con RQ para procesar las tareas de generación en segundo plano.

## Características

- Generación de audio a partir de texto.
- Síntesis de voz mediante Kokoro TTS.
- Procesamiento de trabajos en segundo plano.
- Gestión de tareas mediante Redis y RQ.
- Almacenamiento y descarga de archivos de audio.
- Interfaz web para gestionar las generaciones.
- Arquitectura basada en servicios Docker.

## Tecnologías

| Tecnología | Uso |
|---|---|
| Python | Lenguaje principal |
| Django | Framework web |
| SQLite | Base de datos |
| Redis | Gestión de colas |
| RQ | Procesamiento en segundo plano |
| Kokoro-FastAPI | Motor de síntesis de voz |
| Docker | Contenedorización |
| Docker Compose | Orquestación de servicios |
| Gunicorn | Servidor de aplicaciones |

## Arquitectura

El proyecto utiliza cuatro servicios principales:

- **Web:** aplicación Django servida mediante Gunicorn.
- **Worker:** procesa las tareas de generación de audio.
- **Redis:** administra la cola de trabajos.
- **Kokoro TTS:** convierte texto en voz.

## Requisitos

- Git
- Docker Engine
- Docker Compose

## Instalación

Clona el repositorio:

```bash
git clone https://github.com/JnBenites/JKaudio.git
cd JKaudio
```

Crea el archivo de configuración:

```bash
cp .env.example .env
```

Edita `.env` y configura las variables necesarias:

| Variable | Descripción |
|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta de Django |
| `DJANGO_DEBUG` | Modo de depuración |
| `DJANGO_ALLOWED_HOSTS` | Hosts autorizados |
| `CSRF_TRUSTED_ORIGINS` | Orígenes autorizados para CSRF |
| `REDIS_PASSWORD` | Contraseña de Redis |
| `REDIS_URL` | Dirección de conexión a Redis |
| `KOKORO_API_URL` | Dirección del servicio Kokoro-FastAPI |

La contraseña incluida en `REDIS_URL` debe coincidir con `REDIS_PASSWORD`.

Construye e inicia los servicios:

```bash
docker compose up -d --build
```

Ejecuta las migraciones:

```bash
docker compose run --rm web python manage.py migrate
```

Crea un usuario administrador:

```bash
docker compose run --rm web python manage.py createsuperuser
```

La aplicación estará disponible en:

```text
http://localhost:8000
```

## Administración

Consultar el estado de los servicios:

```bash
docker compose ps
```

Consultar los registros:

```bash
docker compose logs -f
```

Detener los servicios:

```bash
docker compose down
```

## Almacenamiento

- SQLite almacena los datos de la aplicación.
- Los archivos de audio se guardan en el directorio `media/`.
- Redis utiliza almacenamiento persistente mediante volúmenes Docker.
- Kokoro TTS dispone de un volumen para sus datos y modelos.

## Seguridad

No publiques archivos `.env`, contraseñas, claves secretas, bases de datos personales ni archivos privados.

Utiliza `.env.example` como plantilla de configuración.

