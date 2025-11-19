Django CSV Product Importer
 High-Performance Bulk Product Importer (Django + Celery + Redis + PostgreSQL + Docker)

A scalable and production-grade CSV Product Importer built with Django, using Celery workers for background processing and Redis as a message broker.
Designed to handle 500,000+ CSV records without blocking the server.


Features :

 Upload CSV files up to 500,000+ products

 Asynchronous background processing using Celery

 Live progress tracking via Redis

 Optimized bulk PostgreSQL inserts (super fast)

 100% Dockerized (web + worker + beat + redis + postgres)

 REST API + UI front-end

 Clean, modular, scalable architecture


CSV Import Workflow

Upload a CSV file using UI or API

File is streamed → task sent to Celery

Celery worker processes rows in batches (5,000 per batch)

Progress is updated in Redis

UI shows real-time progress

All products stored in PostgreSQL efficiently
