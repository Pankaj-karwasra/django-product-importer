import csv
import json
import os
import traceback
from django.db import connections
from django.conf import settings
from celery import shared_task, Task
from psycopg2.extras import execute_values
import redis
from .models import Product, Webhook
import requests

redis_client = redis.Redis.from_url(settings.REDIS_URL)

BATCH_SIZE = 5000


class ProgressTask(Task):
    def set_progress(self, task_id, progress, status="processing", message=""):
        redis_client.set(
            f"upload_progress:{task_id}",
            json.dumps({"status": status, "progress": progress, "message": message}),
        )


@shared_task(bind=True, base=ProgressTask)
def import_csv_task(self, filepath, task_id):

    # Ensure DB connection is alive
    django_conn = connections["default"]
    django_conn.ensure_connection()
    psycopg_conn = django_conn.connection

    # Open CSV file
    try:
        f = open(filepath, "r", encoding="utf-8")
    except Exception:
        self.set_progress(task_id, 100, "failed", "Cannot open CSV file")
        return {"status": "failed"}

    reader = csv.DictReader(f)

    # -------------------------------
    # UPDATED: CSV header validation
    # price column is optional
    # -------------------------------
    required_cols = {"sku", "name", "description"}
    csv_cols = {h.strip().lower() for h in reader.fieldnames}

    if not required_cols.issubset(csv_cols):
        f.close()
        self.set_progress(task_id, 100, "failed", "Invalid CSV columns")
        return {"status": "failed", "message": "Invalid header"}

    # Count rows
    total = sum(1 for _ in open(filepath, "r", encoding="utf-8")) - 1
    if total <= 0:
        self.set_progress(task_id, 100, "failed", "CSV is empty")
        return {"status": "failed"}

    processed = 0
    self.set_progress(task_id, 0, "processing", "Import started")

    f.seek(0)
    reader = csv.DictReader(f)

    batch = []

    try:
        for row in reader:
            sku = (row.get("sku") or "").strip()
            if not sku:
                processed += 1
                continue

            name = row.get("name") or ""
            description = row.get("description") or ""

            # ---------------------------------------
            # UPDATED: price is optional
            # ---------------------------------------
            price_raw = row.get("price") if "price" in row else None

            try:
                price_val = float(price_raw) if price_raw else None
            except:
                price_val = None

            batch.append((sku, name, description, price_val, True))

            if len(batch) >= BATCH_SIZE:
                upsert_products_batch(psycopg_conn, batch)
                processed += len(batch)
                batch.clear()

                progress = int(processed / total * 100)
                self.set_progress(task_id, progress, "processing", f"Imported {processed}")

        if batch:
            upsert_products_batch(psycopg_conn, batch)
            processed += len(batch)

        self.set_progress(task_id, 100, "completed", f"Imported {processed} rows")

    except Exception as e:
        err = f"{type(e).__name__}: {str(e)}"
        self.set_progress(task_id, 100, "failed", err)
        traceback.print_exc()

    finally:
        f.close()
        try:
            os.remove(filepath)
        except:
            pass

    return {"status": "completed", "processed": processed}


def upsert_products_batch(conn, rows):
    sql = """
    INSERT INTO products_product (sku, name, description, price, active, created_at, updated_at)
    VALUES %s
    ON CONFLICT ON CONSTRAINT unique_lower_sku
    DO UPDATE SET
        sku = EXCLUDED.sku,
        name = EXCLUDED.name,
        description = EXCLUDED.description,
        price = EXCLUDED.price,
        active = EXCLUDED.active,
        updated_at = NOW()
    """

    with conn.cursor() as cur:
        execute_values(
            cur,
            sql,
            rows,
            template="(%s, %s, %s, %s, %s, NOW(), NOW())",
            page_size=1000,
            fetch=False,
        )


@shared_task
def test_webhook_task(webhook_id):
    try:
        wh = Webhook.objects.get(pk=webhook_id)
    except Webhook.DoesNotExist:
        return {"status": "not_found"}

    try:
        resp = requests.post(wh.url, json={"test": True}, timeout=10)
        return {"status": "ok", "status_code": resp.status_code, "body": resp.text[:500]}
    except Exception as e:
        return {"status": "error", "error": str(e)}
