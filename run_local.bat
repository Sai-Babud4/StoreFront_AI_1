@echo off
title RetailIQ Production Server
echo Starting RetailIQ on http://127.0.0.1:8000 ...
python -m uvicorn api.index:app --host 127.0.0.1 --port 8000
pause
