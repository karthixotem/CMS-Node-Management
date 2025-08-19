from django.db import models


class Node(models.Model):
    node_id = models.CharField(primary_key=True, max_length=128)
    ip = models.CharField(max_length=255)
    port = models.IntegerField()
    status = models.CharField(max_length=32, default='disconnected')
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.node_id


class Upload(models.Model):
    filename = models.CharField(max_length=255)
    originalname = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class UploadStatus(models.Model):
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE)
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    status = models.CharField(max_length=32) # PENDING / SUCCESS / FAILED
    detail = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

