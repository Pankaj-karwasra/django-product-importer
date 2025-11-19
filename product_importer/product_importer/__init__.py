from .celery_app import app as celery_app

__all__ = ("celery_app",)





# docker run -d -p 6379:6379 redis
#celery -A product_importer.celery worker --loglevel=info --pool=solo