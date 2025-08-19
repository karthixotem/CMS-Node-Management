from datetime import datetime


def log(*args):
    print(f"[NODE {datetime.utcnow().isoformat()}]", *args, flush=True)

