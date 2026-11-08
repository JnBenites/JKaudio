
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from rq import SimpleWorker

from apps.generator.queue import get_generation_queue
from apps.generator.exception_handlers import handle_abandoned_generation


def main():
    queue = get_generation_queue()

    worker = SimpleWorker(
        [queue],
        connection=queue.connection,
        exception_handlers=[
            handle_abandoned_generation
        ]
    )

    print("JKaudio SimpleWorker iniciado.")
    print(f"Escuchando la cola: {queue.name}")
    print("Manejador de trabajos abandonados: activo.")

    worker.work()


if __name__ == "__main__":
    main()
