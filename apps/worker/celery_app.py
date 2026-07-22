from celery import Celery

from mei.shared.config import get_settings

settings = get_settings()

celery_app = Celery(
    "mei",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "apps.worker.tasks.collect",
        "apps.worker.tasks.parse",
        "apps.worker.tasks.translate",
        "apps.worker.tasks.extract",
        "apps.worker.tasks.resolve_entities",
        "apps.worker.tasks.verify",
        "apps.worker.tasks.calculate_risks",
        "apps.worker.tasks.update_scenarios",
        "apps.worker.tasks.generate_reports",
        "apps.worker.tasks.dispatch_notifications",
        "apps.worker.tasks.investigate",
        "apps.worker.tasks.multi_model_review",
        "apps.worker.tasks.imagery",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    # Split by queue so workers can be scaled independently per section 31.3
    # of the implementation design (collection / browser / extraction /
    # analysis / reporting).
    task_routes={
        "apps.worker.tasks.collect.*": {"queue": "collection"},
        "apps.worker.tasks.parse.*": {"queue": "extraction"},
        "apps.worker.tasks.translate.*": {"queue": "extraction"},
        "apps.worker.tasks.extract.*": {"queue": "extraction"},
        "apps.worker.tasks.resolve_entities.*": {"queue": "extraction"},
        "apps.worker.tasks.verify.*": {"queue": "analysis"},
        "apps.worker.tasks.calculate_risks.*": {"queue": "analysis"},
        "apps.worker.tasks.update_scenarios.*": {"queue": "analysis"},
        "apps.worker.tasks.generate_reports.*": {"queue": "reporting"},
        "apps.worker.tasks.dispatch_notifications.*": {"queue": "reporting"},
        "apps.worker.tasks.investigate.*": {"queue": "analysis"},
        "apps.worker.tasks.multi_model_review.*": {"queue": "analysis"},
        "apps.worker.tasks.imagery.*": {"queue": "extraction"},
    },
)

from apps.worker import schedules  # noqa: E402

celery_app.conf.beat_schedule = schedules.BEAT_SCHEDULE
