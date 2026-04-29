@echo off
echo ================================================
echo  AstroSignature Tool — Auto Installer v1
echo ================================================
echo.

SET DOWNLOADS=%USERPROFILE%\Downloads
SET TXTFILE=%DOWNLOADS%\AstroSignature.txt
SET PYFILE=%DOWNLOADS%\AstroSignature.py
SET DEST=%APPDATA%\siril\scripts\

:: Step 1 — Rename .txt to .py if needed
IF EXIST "%TXTFILE%" (
    echo Found AstroSignature.txt in Downloads — renaming to .py...
    IF EXIST "%PYFILE%" del "%PYFILE%"
    ren "%TXTFILE%" "AstroSignature.py"
    echo   Renamed successfully.
    echo.
) ELSE IF EXIST "%PYFILE%" (
    echo Found AstroSignature.py in Downloads — ready to install.
    echo.
) ELSE (
    echo ERROR: AstroSignature.txt or AstroSignature.py not found in:
    echo   %DOWNLOADS%
    echo.
    echo Please download the file to your Downloads folder first.
    echo.
    pause
    exit /b 1
)

:: Step 2 — Copy to Siril scripts location
echo Copying to: %DEST%
IF NOT EXIST "%DEST%" mkdir "%DEST%"
copy /Y "%PYFILE%" "%DEST%" >nul
IF %ERRORLEVEL%==0 (
    echo   SUCCESS
) ELSE (
    echo   FAILED — check folder permissions
    pause
    exit /b 1
)

:: Step 3 — Clean up Downloads folder
echo.
echo Cleaning up Downloads folder...
del "%PYFILE%"
echo   AstroSignature.py removed from Downloads.

echo.
echo ================================================
echo  Installation complete!
echo  Refresh scripts in Siril:
echo  Preferences ^> Scripts ^> refresh button ^> Apply
echo ================================================
echo.
pause
