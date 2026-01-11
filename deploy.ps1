# PowerShell deployment script for ServiceNow Consultant (Windows)

Write-Host "🚀 ServiceNow Consultant Deployment Script" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "⚠️  Warning: .env file not found" -ForegroundColor Yellow
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "Created .env from .env.example" -ForegroundColor Yellow
        Write-Host "Please update .env with your API keys" -ForegroundColor Yellow
    } else {
        Write-Host "❌ .env.example not found. Please create .env manually." -ForegroundColor Red
        exit 1
    }
}

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Cyan
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path venv)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Install/upgrade dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
Write-Host "Creating necessary directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path chroma_db | Out-Null
New-Item -ItemType Directory -Force -Path user_context_data | Out-Null
New-Item -ItemType Directory -Force -Path .cursor | Out-Null

# Check environment variables
Write-Host "Checking environment variables..." -ForegroundColor Cyan
$requiredVars = @("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY")
$missingVars = @()

foreach ($var in $requiredVars) {
    $envContent = Get-Content .env -ErrorAction SilentlyContinue
    if ($envContent -notmatch "^${var}=") {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "⚠️  Missing environment variables: $($missingVars -join ', ')" -ForegroundColor Yellow
    Write-Host "Please add them to your .env file" -ForegroundColor Yellow
}

# Run basic health check
Write-Host "Running health check..." -ForegroundColor Cyan
python -c "
import sys
try:
    from agent import get_agent
    from knowledge_base import get_embeddings
    print('✅ Core modules import successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

Write-Host ""
Write-Host "✅ Deployment preparation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  streamlit run streamlit_app.py" -ForegroundColor White
Write-Host ""
Write-Host "Or use Docker:" -ForegroundColor Cyan
Write-Host "  docker-compose up -d" -ForegroundColor White
