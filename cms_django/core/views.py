import httpx
import os
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser

from .models import Node, Upload, UploadStatus
from .serializers import RegisterNodeSerializer

channel_layer = get_channel_layer()


async def emit(event, data):
    """
    Broadcasts an event to the 'dashboard' channel group asynchronously.

    Args:
        event (str): Event type name.
        data (dict): Event payload to send to the group.
    """

    await channel_layer.group_send('dashboard', { 'type': 'push_event', 'data': { 'event': event, **data }})


def emit_sync(event, data):
    """
    Synchronous wrapper around `emit()` for broadcasting events.

    Args:
        event (str): Event type name.
        data (dict): Event payload to send.
    """

    async_to_sync(emit)(event, data)


@api_view(['POST'])
def register_node(request):
    """
    Registers or updates a node in the system when it connects.
    Also notifies the dashboard about the node's 'connected' status.
    """

    ser = RegisterNodeSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    d = ser.validated_data
    node, _ = Node.objects.update_or_create(
        node_id=d['nodeId'],
        defaults={'ip': d['ip'], 'port': d['port'], 'status': 'connected'}
    )
    emit_sync('node:update', { 'nodeId': node.node_id, 'status': 'connected', 'ip': node.ip, 'port': node.port })
    return JsonResponse({ 'ok': True })


@api_view(['POST'])
def disconnect_node(request, node_id: str):
    """
    Marks a node as disconnected and notifies the dashboard.

    Args:
        node_id (str): The ID of the node being disconnected.
    """

    Node.objects.filter(node_id=node_id).update(status='disconnected')
    emit_sync('node:update', { 'nodeId': node_id, 'status': 'disconnected' })
    return JsonResponse({ 'ok': True })


@api_view(['GET'])
def list_nodes(request):
    """
    Retrieves a list of all nodes with their current status
    and last upload status (if any).
    """

    with connection.cursor() as cur:
        cur.execute('''
          SELECT n.node_id, n.ip, n.port, n.status,
            (
              SELECT CONCAT(us.status, COALESCE(CONCAT(' (', us.detail, ')'), ''))
              FROM core_uploadstatus us
              WHERE us.node_id = n.node_id
              ORDER BY us.updated_at DESC, us.id DESC
              LIMIT 1
            ) AS last_upload_status
          FROM core_node n
          ORDER BY n.node_id ASC
        ''')
        rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]

    return JsonResponse(rows, safe=False)


@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_to_all(request):
    """
    Uploads a file and distributes it to all connected nodes.
    Tracks status for each node and broadcasts events to the dashboard.
    """

    f = request.FILES.get('file')
    if not f:
        return JsonResponse({ 'error': 'file field required' }, status=400)

    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    filename = f"{int(__import__('time').time())}-{f.name}"
    fpath = os.path.join(settings.MEDIA_ROOT, filename)
    with open(fpath, 'wb') as out:
        for chunk in f.chunks():
            out.write(chunk)

    upl = Upload.objects.create(filename=filename, originalname=f.name)
    nodes = list(Node.objects.filter(status='connected').values('node_id','ip','port'))

    for n in nodes:
        UploadStatus.objects.create(upload=upl, node_id=n['node_id'], status='PENDING', detail='queued')
        emit_sync('upload:status', { 'uploadId': upl.id, 'nodeId': n['node_id'], 'status': 'PENDING', 'detail': 'queued' })

    # propagate asynchronously (fire-and-forget)
    async_to_sync(_propagate)(upl.id, filename, f.name, nodes)

    return JsonResponse({ 'ok': True, 'uploadId': upl.id, 'filename': filename, 'originalname': f.name, 'nodes': [n['node_id'] for n in nodes] })


async def _propagate(upload_id: int, filename: str, originalname: str, nodes: list[dict]):
    """
    Asynchronously sends the uploaded file to each connected node
    and updates the upload status for each node.

    Args:
        upload_id (int): The ID of the upload.
        filename (str): The saved filename on the server.
        originalname (str): The original filename uploaded by user.
        nodes (list[dict]): List of connected nodes with {node_id, ip, port}.
    """

    filepath = os.path.join(settings.MEDIA_ROOT, filename)
    async with httpx.AsyncClient(timeout=20.0) as client:
        for n in nodes:
            url = f"http://{n['ip']}:{n['port']}/upload"
            files = {'file': (originalname, open(filepath, 'rb'), 'application/octet-stream')}
            data = {'uploadId': str(upload_id)}
            try:
                r = await client.post(url, data=data, files=files)
                j = r.json()
                status = 'SUCCESS' if j.get('ok') else 'FAILED'
                detail = j.get('message', '')
            except Exception as e:
                status = 'FAILED'
                detail = str(e)

            await sync_to_async(
                lambda: UploadStatus.objects.filter(upload_id=upload_id, node_id=n['node_id']).update(
                    status=status,
                    detail=detail
                )
            )()

            # 👇 FIX: use emit directly
            await emit('upload:status', {
                'uploadId': upload_id,
                'nodeId': n['node_id'],
                'status': status,
                'detail': detail
            })


@api_view(['POST'])
def upload_status_event(request):
    """
    Updates the upload status for a given node and upload,
    and broadcasts the change to the dashboard.
    """

    uploadId = int(request.data.get('uploadId'))
    nodeId = request.data.get('nodeId')
    status = request.data.get('status')
    detail = request.data.get('detail')
    UploadStatus.objects.filter(upload_id=uploadId, node_id=nodeId).update(status=status, detail=detail)
    emit_sync('upload:status', { 'uploadId': uploadId, 'nodeId': nodeId, 'status': status, 'detail': detail })
    return JsonResponse({ 'ok': True })

