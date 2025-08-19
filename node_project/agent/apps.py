from django.apps import AppConfig
from django.conf import settings
import threading, time, httpx


class AgentConfig(AppConfig):
    """
    Django application configuration for the 'agent' app.
    Handles automatic node registration with the CMS on startup.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agent'

    def ready(self):
        """
        Called when the Django app is ready.
        Spawns a background thread that registers the node with the CMS.
        """

        def _register_once():
            """
            Registers the current node with the CMS after a short delay.
            Uses settings.APP_ENV values for CMS_URL, NODE_ID, IP, and PORT.
            """

            try:
                time.sleep(0.5)
                cms = settings.APP_ENV['CMS_URL']
                payload = { 'nodeId': settings.APP_ENV['NODE_ID'], 'ip': settings.APP_ENV['IP'], 'port': int(settings.APP_ENV['PORT']) }
                with httpx.Client(timeout=10.0) as c:
                    c.post(f"{cms}/api/nodes/register", json=payload)
            except Exception:
                pass
        threading.Thread(target=_register_once, daemon=True).start()

