from rest_framework import serializers
from .models import Node
from .models import Upload
from .models import UploadStatus


class RegisterNodeSerializer(serializers.Serializer):
    nodeId = serializers.CharField()
    ip = serializers.CharField()
    port = serializers.IntegerField()

