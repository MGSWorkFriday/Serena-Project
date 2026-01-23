d:
cd D:\Github\nwevrijdag\pythonbleakgui_server

rem Kies hier de gewenste versie van de estimator
rem set RESP_RR_VERSION=v1_default
set RESP_RR_VERSION=v2_experiment

uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 1
