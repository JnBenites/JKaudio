@echo off
cd /d C:\Users\k\Documents\DESARROLLO\JKaudio

.venv\Scripts\python.exe manage.py cleanup_audio >> logs_cleanup.txt 2>&1