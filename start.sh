#!/bin/bash
cd /root/memories-sorted
exec /root/memories-sorted/venv/bin/python3 api.py >> /tmp/memories.log 2>&1