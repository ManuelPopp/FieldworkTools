@echo off
setlocal enabledelayedexpansion

:: Define base Git directory
set "GITROOT=C:\Users\dme\git"

:: Define source script paths
set "SRC_PLOTPLANNER=%GITROOT%\FieldworkTools\QGIS\plotplanner.py"
set "SRC_MERGELAS=%GITROOT%\FieldworkTools\QGIS\mergelas.py"
set "SRC_CROPLAS=%GITROOT%\FieldworkTools\QGIS\croplas.py"

:: Define destination script directory
set "DESTDIR=C:\Users\dme\AppData\Roaming\QGIS\QGIS3\profiles\default\processing\scripts"
set "DEST_PLOTPLANNER=%DESTDIR%\plotplanner.py"
set "DEST_CROPLAS=%DESTDIR%\croplas.py"
set "DEST_MERGELAS=%DESTDIR%\mergelas.py"

:: Go to repo directory
pushd "%GITROOT%\FieldworkTools"

echo Pulling latest changes from Git...
git fetch origin
git reset --hard origin/main

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Git pull failed. Check your internet connection or repo status.
    pause
    popd
    exit /b 1
)
echo [OK] Git pull successful.

:: Copy plotplanner.py
echo Copying plotplanner.py...
copy /y "%SRC_PLOTPLANNER%" "%DEST_PLOTPLANNER%" >nul
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to copy plotplanner.py
    pause
    popd
    exit /b 1
)
echo [OK] plotplanner.py copied.

:: Copy mergelas.py
echo Copying mergelas.py...
copy /y "%SRC_MERGELAS%" "%DEST_MERGELAS%" >nul
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to copy mergelas.py
    pause
    popd
    exit /b 1
)
echo [OK] mergelas.py copied.

:: Copy croplas.py
echo Copying croplas.py...
copy /y "%SRC_CROPLAS%" "%DEST_CROPLAS%" >nul
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to copy croplas.py
    pause
    popd
    exit /b 1
)
echo [OK] croplas.py copied.

:: Convert backslashes to forward slashes for use in Python-compatible string
set "GITROOT_PY=%GITROOT:\=/%"

:: Define the PowerShell replacement command
set "REPLACEMENT=script_dir = \"%GITROOT_PY%/FieldworkTools/R\""

echo Updating script_dir path inside all scripts...

:: Update plotplanner.py
powershell -Command "(Get-Content -Raw '%DEST_PLOTPLANNER%') -replace 'script_dir = \\\".*?\\\"', '%REPLACEMENT%' | Set-Content -Encoding UTF8 '%DEST_PLOTPLANNER%'"

IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to update plotplanner.py
    pause
    popd
    exit /b 1
)

:: Update mergelas.py
powershell -Command "(Get-Content -Raw '%DEST_MERGELAS%') -replace 'script_dir = \\\".*?\\\"', '%REPLACEMENT%' | Set-Content -Encoding UTF8 '%DEST_MERGELAS%'"

IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to update mergelas.py
    pause
    popd
    exit /b 1
)

:: Update croplas.py
powershell -Command "(Get-Content -Raw '%DEST_CROPLAS%') -replace 'script_dir = \\\".*?\\\"', '%REPLACEMENT%' | Set-Content -Encoding UTF8 '%DEST_CROPLAS%'"

IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to update croplas.py
    pause
    popd
    exit /b 1
)

echo [OK] script_dir paths updated.

popd
echo.
echo [SUCCESS] Update completed successfully.
timeout /t 5 >nul
exit /b 0