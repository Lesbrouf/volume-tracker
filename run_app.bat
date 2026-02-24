@echo off 
echo =================================================== 
echo   Volume Tracker App - Startup Script 
echo =================================================== 
echo. 
echo [1/3] Checking Python Requirements... 
pip install -r requirements.txt 
echo. 
echo [2/3] Checking Frontend Dependencies... 
if not exist frontend\node_modules\ (cd frontend & call npm install & cd ..) 
echo. 
echo [3/3] Launching App... 
python launcher.py 
pause
