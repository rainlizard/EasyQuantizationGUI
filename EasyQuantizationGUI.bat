@echo off
setlocal EnableDelayedExpansion

set "APP_ENTRY=EasyQuantizationGUI.py"
set "VENV_DIR=venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "REQUIREMENTS=requirements.txt"

REM ── Python availability ────────────────────────────────────────────────────
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found. Please install Python and ensure it is on your PATH.
    goto :error
)

REM ── pip availability ───────────────────────────────────────────────────────
python -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] pip not found. Installing via ensurepip...
    python -m ensurepip --default-pip
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install pip.
        goto :error
    )
) else (
    python -m pip install --upgrade pip >nul 2>&1
)

REM ── Virtual environment setup ──────────────────────────────────────────────
if not exist "%VENV_DIR%\" (
    echo [INFO] Virtual environment not found. Creating "%VENV_DIR%"...
    python -m venv "%VENV_DIR%"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        goto :error
    )

    call "%VENV_ACTIVATE%"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to activate virtual environment.
        goto :error
    )

    echo [INFO] Installing dependencies from "%REQUIREMENTS%"...
    pip install -r "%REQUIREMENTS%"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Dependency installation failed.
        goto :error
    )

    echo [INFO] Setup complete.
    echo.
) else (
    call "%VENV_ACTIVATE%"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to activate virtual environment.
        goto :error
    )
)

REM ── Launch application ─────────────────────────────────────────────────────
echo [INFO] Starting %APP_ENTRY%...
python "%APP_ENTRY%"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Application exited with an error (code: %ERRORLEVEL%).
    goto :error
)

goto :end

:error
echo.
echo Press any key to exit...
pause >nul
exit /b 1

:end
endlocal
exit /b 0