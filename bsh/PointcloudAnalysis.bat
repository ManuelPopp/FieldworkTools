@echo off
REM ===============================
REM Batch script to run Python report
REM ===============================

REM Get folder of this batch script
SET "SCRIPT_DIR=%~dp0"

REM Build path to Python script (relative to batch script)
SET "PY_SCRIPT=%SCRIPT_DIR%..\py3\pointcloud_report.py"

REM Optional: normalize path (remove ..)
FOR /F "delims=" %%I IN ('CD') DO SET "CURDIR=%%I"
PUSHD "%SCRIPT_DIR%..\py3"
SET "PY_SCRIPT_FULL=%CD%\pointcloud_report.py"
POPD

REM Run Python script
python "%PY_SCRIPT_FULL%"