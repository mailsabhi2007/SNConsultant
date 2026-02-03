@echo off
REM Deployment script for ServiceNow Consultant Multi-Agent System (Windows)

echo ==========================================
echo ServiceNow Consultant Deployment Script
echo ==========================================
echo.

REM Step 1: Check prerequisites
echo [*] Checking prerequisites...

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [X] Python not found. Please install Python 3.9+
    exit /b 1
)
echo [+] Python found

where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Node.js not found. Frontend deployment will be skipped.
    set DEPLOY_FRONTEND=0
) else (
    echo [+] Node.js found
    set DEPLOY_FRONTEND=1
)

echo.

REM Step 2: Backup database
echo [*] Creating database backup...
if exist data\app.db (
    set BACKUP_FILE=data\app.db.backup.%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
    set BACKUP_FILE=%BACKUP_FILE: =0%
    copy data\app.db "%BACKUP_FILE%" >nul
    echo [+] Database backed up to %BACKUP_FILE%
) else (
    echo [!] No existing database found. Skipping backup.
)

echo.

REM Step 3: Install Python dependencies
echo [*] Installing Python dependencies...
if exist venv (
    call venv\Scripts\activate
) else (
    echo [*] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
)

pip install -r requirements.txt >nul 2>&1
echo [+] Python dependencies installed

echo.

REM Step 4: Run database migration
echo [*] Running database migration...
python database.py
if %ERRORLEVEL% EQU 0 (
    echo [+] Database migration completed
) else (
    echo [X] Database migration failed
    exit /b 1
)

echo.

REM Step 5: Deploy frontend
if %DEPLOY_FRONTEND% EQU 1 (
    echo [*] Installing frontend dependencies...
    cd frontend
    call npm install >nul 2>&1
    echo [+] Frontend dependencies installed

    echo [*] Building frontend...
    call npm run build >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [+] Frontend built successfully
    ) else (
        echo [X] Frontend build failed
        cd ..
        exit /b 1
    )
    cd ..
) else (
    echo [!] Skipping frontend deployment (Node.js not found)
)

echo.

REM Step 6: Initialize configuration
echo [*] Initializing multi-agent configuration...
python -c "from user_config import set_multi_agent_rollout_percentage, get_system_config; current = get_system_config('multi_agent_rollout_percentage'); set_multi_agent_rollout_percentage(0) if current is None else None; print(f'Rollout initialized to 0%%' if current is None else f'Rollout already set to {current}%%')"
echo [+] Configuration initialized

echo.

REM Step 7: Display summary
echo ==========================================
echo Deployment Summary
echo ==========================================
echo.
echo [+] Backend deployed successfully
if %DEPLOY_FRONTEND% EQU 1 (
    echo [+] Frontend built successfully
)
echo [+] Database migrated
echo [+] Configuration initialized

echo.
echo Next steps:
echo 1. Configure environment variables in .env
echo 2. Make first user superadmin (see DEPLOYMENT_GUIDE.md)
echo 3. Start the backend:
echo    uvicorn api.main:app --reload
echo 4. Access at: http://localhost:8000
echo.
echo [*] For production deployment, see DEPLOYMENT_GUIDE.md
echo.

pause
