from celery.schedules import crontab

# System schedules per implementation design section 24.1. Task names are
# referenced by string to avoid import-order coupling with celery_app.
BEAT_SCHEDULE = {
    "collect-critical-feeds": {
        "task": "apps.worker.tasks.collect.collect_critical_feeds",
        "schedule": crontab(minute="*/10"),
    },
    "collect-normal-feeds": {
        "task": "apps.worker.tasks.collect.collect_normal_feeds",
        "schedule": crontab(minute=0),
    },
    "retry-failed-endpoints": {
        "task": "apps.worker.tasks.collect.retry_failed_endpoints",
        "schedule": crontab(minute="*/30"),
    },
    "reevaluate-unresolved-claims": {
        "task": "apps.worker.tasks.verify.reevaluate_unresolved_claims",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    "recalculate-active-conflict-risks": {
        "task": "apps.worker.tasks.calculate_risks.recalculate_active_conflict_risks",
        "schedule": crontab(minute=0),
    },
    "refresh-country-indicators": {
        "task": "apps.worker.tasks.calculate_risks.refresh_country_indicators",
        "schedule": crontab(minute=0, hour=3),
    },
    "generate-daily-brief": {
        "task": "apps.worker.tasks.generate_reports.generate_daily_brief",
        "schedule": crontab(minute=0, hour=5),
    },
    "generate-weekly-outlook": {
        "task": "apps.worker.tasks.generate_reports.generate_weekly_outlook",
        "schedule": crontab(minute=0, hour=5, day_of_week=1),
    },
    "evaluate-monitors": {
        "task": "apps.worker.tasks.dispatch_notifications.evaluate_monitors",
        "schedule": crontab(minute="*/10"),
    },
    "audit-source-failures": {
        "task": "apps.worker.tasks.collect.audit_source_failures",
        "schedule": crontab(minute=0, hour=6),
    },
    "evaluate-due-forecasts": {
        "task": "apps.worker.tasks.update_scenarios.evaluate_due_forecasts",
        "schedule": crontab(minute=0, hour=6),
    },
    "archive-old-raw-data": {
        "task": "apps.worker.tasks.collect.archive_old_raw_data",
        "schedule": crontab(minute=0, hour=4, day_of_week=0),
    },
}
