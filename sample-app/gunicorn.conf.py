
"""Gunicorn configuration for the TechStore sample application."""

import os

bind = "0.0.0.0:5000"

# Experiment variables
workers = int(os.environ.get("WORKERS", "2"))
threads = int(os.environ.get("THREADS", "2"))

timeout = 30

# Docker logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
