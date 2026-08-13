@echo off
cd /d "%~dp0"
python publish_build.py %*
pause