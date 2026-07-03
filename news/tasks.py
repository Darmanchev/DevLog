from celery import shared_task


@shared_task
def debug_task(message='ping'):
    return f'Celery received: {message}'
