@echo off
REM Check if pip is installed and show output only if it needs to be installed
python -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing pip...
    python -m ensurepip --default-pip
) else (
    python -m pip install --upgrade pip >nul 2>&1
)

REM Check if virtual environment exists, create if it doesn't
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing requirements...
    pip install -r requirements.txt
    echo Setup complete!
    echo.
) else (
    call venv\Scripts\activate
)

REM Run the application
python EasyQuantizationGUI.py

REM Keep the window open if there's an error
if %ERRORLEVEL% neq 0 (
    pause
)