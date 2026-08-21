"""Celery application factory.

Usage in Flask app:
    from tasks import init_celery
    celery = init_celery(app)
"""

from celery import Celery


def make_celery(app=None):
    """Create a Celery instance from Flask app config.

    If app is provided, config is loaded immediately.
    Otherwise, call celery.conf.update(app.config) later.
    """
    celery = Celery(
        __name__,
        broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
               if app else 'redis://localhost:6379/0',
    )

    if app:
        celery.conf.update(app.config)
        # Ensure task modules are imported
        celery.autodiscover_tasks(['tasks'])
    else:
        celery.conf.update(
            broker_url='redis://localhost:6379/0',
            result_backend='redis://localhost:6379/1',
            accept_content=['json'],
            task_serializer='json',
            result_serializer='json',
            timezone='Asia/Tehran',
            task_track_started=True,
            task_time_limit=300,
        )

    return celery


def init_celery(app):
    """Initialize Celery with a Flask app and store reference on app."""
    celery = make_celery(app)
    app.celery = celery
    return celery
