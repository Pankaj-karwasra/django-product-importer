import os
import uuid
import json
import redis
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Product, Webhook
from .serializers import ProductSerializer, WebhookSerializer
from .tasks import import_csv_task, test_webhook_task

# Redis connection for progress
redis_client = redis.Redis.from_url(settings.REDIS_URL)

def ui_view(request):
    return render(request, 'products/ui.html')

@api_view(['POST'])
def upload_csv(request):
    """
    Accepts multipart file upload, saves to tmp, triggers Celery import task, returns task_id.
    """
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return HttpResponseBadRequest("Missing file")

    # save to temporary location
    tmp_dir = os.path.join(settings.BASE_DIR, 'tmp_uploads')
    os.makedirs(tmp_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}_{uploaded_file.name}"
    fpath = os.path.join(tmp_dir, fname)
    with open(fpath, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    # Create a task id for progress tracking
    task_id = uuid.uuid4().hex
    # initialize progress in redis
    redis_client.set(f"upload_progress:{task_id}", json.dumps({"status":"queued","progress":0,"message":"Queued"}))
    # trigger celery task
    import_csv_task.delay(fpath, task_id)
    return JsonResponse({"task_id": task_id})

def upload_status(request, task_id):
    key = f"upload_progress:{task_id}"
    data = redis_client.get(key)
    if not data:
        return JsonResponse({"status":"unknown"}, status=404)
    return JsonResponse(json.loads(data))

# Products endpoints
class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-updated_at')
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET
        sku = q.get('sku')
        name = q.get('name')
        active = q.get('active')
        desc = q.get('description')
        if sku:
            qs = qs.filter(sku__icontains=sku)
        if name:
            qs = qs.filter(name__icontains=name)
        if active in ('true','false'):
            qs = qs.filter(active=(active=='true'))
        if desc:
            qs = qs.filter(description__icontains=desc)
        return qs

class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

@api_view(['POST'])
def bulk_delete_products(request):
    confirm = request.data.get('confirm')
    if confirm != True and confirm != "true":
        return Response({"detail": "You must confirm deletion by sending { confirm: true }"}, status=status.HTTP_400_BAD_REQUEST)
    count, _ = Product.objects.all().delete()
    return Response({"deleted_count": count})

# Webhooks
class WebhookListCreateView(generics.ListCreateAPIView):
    queryset = Webhook.objects.all().order_by('-created_at')
    serializer_class = WebhookSerializer

class WebhookRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer

@api_view(['POST'])
def webhook_test(request, pk):
    try:
        wh = Webhook.objects.get(pk=pk)
    except Webhook.DoesNotExist:
        return Response(status=404)
    # trigger async test
    task_id = test_webhook_task.delay(wh.id)
    return Response({"task_id": task_id})
