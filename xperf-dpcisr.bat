@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

:: Check for administrator privileges
DISM > nul 2>&1 || echo error: administrator privileges required >&2 && pause && exit /b 1

:: Check for xperf
where xperf.exe > nul 2>&1
if not %errorlevel% == 0 (
    echo Error: Xperf not found in path. Install "Windows Performance Toolkit" from the ADK >&2
    echo https://learn.microsoft.com/en-us/windows-hardware/get-started/adk-install
    exit /b 1
)

:: Get current date-time stamp using PowerShell (compatible with Windows 11 24H2)
for /f "delims=" %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm"') do set date_time=%%a
set "log_folder=logs\%date_time%"

:: Create log folder
mkdir "%log_folder%"

:: Capture Settings
set "method=dpcisr"
set /p "dtime=Enter Capture Delay (sec): "
set /p "ctime=Enter Capture Time (sec): "
cls

echo info: starting in %dtime%s
timeout /t %dtime% /nobreak >nul

:: Capture notification
powershell -c "[console]::beep(500, 350)"

:: Start Capture
echo info: Capture for %ctime%s
xperf -on base+interrupt+dpc
timeout /t %ctime% /nobreak

:: Stop Capture
xperf -stop

:: Save output in log folder
set "report_file=%log_folder%\report-%date_time%.txt"
set "etl_file=%log_folder%\kernel-%date_time%.etl"

xperf -i "C:\kernel.etl" -o "%report_file%" -a %method%
move "C:\kernel.etl" "%etl_file%"

:: Save data
(
    echo Capture Delay: %dtime% seconds
    echo Capture Duration: %ctime% seconds
    echo Total Capture Time: %dtime% + %ctime% seconds
    echo Capture Timestamp: %date_time%
    echo Xperf Measurement: %method%
) > "%log_folder%\info-%date_time%.txt"

:: Create summary.txt in the same folder
cls
set "summary_file=%log_folder%\summary-%date_time%.txt"
set "py_script=analyze.exe"
if exist "%py_script%" (
    echo [-] Running python script...
    echo.
    echo [-] Capture Delay: %dtime% seconds
    echo [-] Capture Duration: %ctime% seconds
    echo.
    "%py_script%" "%report_file%" "%summary_file%"
) else (
    echo Error: Python analysis script not found 
)

powershell -c "[console]::beep(500, 350)"
pause
exit /b 0