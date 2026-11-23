"""Gunicorn settings. Worker/thread counts are experiment variables:
a single Python process can use only about 1 CPU core (GIL), so the number
of workers decides how much CPU the app can actually consume."""
import glob
import os

bind = "0.0.0.0:5000"
workers = int(os.environ.get("WORKERS", "2"))
threads = int(os.environ.get("THREADS", "4"))
timeout = 30
accesslog = "-"


def on_starting(server):
    # Clear stale Prometheus multiprocess files from a previous run.
    path = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if path:
        os.makedirs(path, exist_ok=True)
        for f in glob.glob(os.path.join(path, "*.db")):
            os.remove(f)


def child_exit(server, worker):
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        from prometheus_client import multiprocess
        multiprocess.mark_process_dead(worker.pid)
