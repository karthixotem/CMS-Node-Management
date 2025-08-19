import httpx
import os
import time
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .utils import log


# Create your views here.

@csrf_exempt
def health(request):
    """
    Health check endpoint for the agent service.

    Returns:
        JsonResponse: {"ok": True} if the service is running.
    """

    return JsonResponse({ 'ok': True })

@csrf_exempt
def upload(request):
    """
    Handles file uploads sent to this agent node.
    - Stores the file locally in MEDIA_ROOT with a timestamped filename.
    - Logs the upload.
    - Notifies the CMS about upload status (if CMS_URL and uploadId are available).

    Args:
        request (HttpRequest): Incoming HTTP request with multipart/form-data.

    Returns:
        JsonResponse: Success or error response depending on upload handling.
    """

    if request.method != 'POST':
        return JsonResponse({ 'error': 'POST required' }, status=405)
    f = request.FILES.get('file')
    uploadId = request.POST.get('uploadId')
    if not f:
        return JsonResponse({ 'error': 'file required' }, status=400)
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    fname = f"{int(time.time())}-{f.name}"
    with open(os.path.join(settings.MEDIA_ROOT, fname), 'wb') as out:
        for chunk in f.chunks(): out.write(chunk)
    log(f"Stored file {fname} (uploadId={uploadId})")

    if settings.APP_ENV['CMS_URL'] and uploadId:
        try:
            with httpx.Client(timeout=10.0) as c:
                c.post(f"{settings.APP_ENV['CMS_URL']}/api/events/upload-status", json={
                    'uploadId': int(uploadId),
                    'nodeId': settings.APP_ENV['NODE_ID'],
                    'status': 'SUCCESS',
                    'detail': 'stored'
                })
        except Exception:
            pass
    return JsonResponse({ 'ok': True, 'message': 'stored' })

