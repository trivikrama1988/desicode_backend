# Save this as get_url.ps1 and run: .\get_url.ps1

# Clear screen
Clear-Host

# Colors
$Green = [ConsoleColor]::Green
$Cyan = [ConsoleColor]::Cyan
$Yellow = [ConsoleColor]::Yellow

Write-Host "🚀 ASPY Backend - Live URL Generator" -ForegroundColor $Green
Write-Host "=" * 60 -ForegroundColor $Cyan

# Check if backend is running
Write-Host "`n🔍 Checking backend..." -ForegroundColor $Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend is running" -ForegroundColor $Green
    }
} catch {
    Write-Host "❌ Backend not running at localhost:8000" -ForegroundColor Red
    Write-Host "   Starting backend now..." -ForegroundColor $Yellow

    # Start backend in background
    Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PWD'; uvicorn app.main:app --reload`""

    Write-Host "   Waiting 5 seconds for backend to start..." -ForegroundColor $Yellow
    Start-Sleep -Seconds 5
}

# Start ngrok
Write-Host "`n🌐 Starting ngrok tunnel..." -ForegroundColor $Cyan
Write-Host "   This will show your public URL" -ForegroundColor $Yellow
Write-Host "-" * 40 -ForegroundColor $Cyan

# Run ngrok
$ngrokProcess = Start-Process -FilePath "ngrok" -ArgumentList "http 8000" -NoNewWindow -PassThru

# Wait a moment then get URL
Start-Sleep -Seconds 3

try {
    Write-Host "`n📡 Getting your public URL..." -ForegroundColor $Cyan
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 5

    if ($tunnels.tunnels) {
        $publicUrl = $tunnels.tunnels[0].public_url
        Write-Host "`n🎉 YOUR LIVE API URL:" -ForegroundColor $Green
        Write-Host "=" * 40 -ForegroundColor $Green
        Write-Host "🌐 $publicUrl" -ForegroundColor White -BackgroundColor DarkBlue
        Write-Host "📚 Docs: $publicUrl/docs" -ForegroundColor $Cyan
        Write-Host "🩺 Health: $publicUrl/health" -ForegroundColor $Cyan
        Write-Host "📋 API Base: $publicUrl/api/v1" -ForegroundColor $Cyan
        Write-Host "=" * 40 -ForegroundColor $Green

        # Copy to clipboard
        Set-Clipboard -Value $publicUrl
        Write-Host "📋 URL copied to clipboard!" -ForegroundColor $Green

        # Generate share message
        Write-Host "`n📤 Share this with frontend team:" -ForegroundColor $Yellow
        Write-Host "-" * 40 -ForegroundColor $Yellow
        Write-Host @"

🚀 ASPY Backend API - Live URL
===============================

🌐 Base URL: $publicUrl/api/v1
📚 Documentation: $publicUrl/docs
🩺 Health Check: $publicUrl/health

Quick test:
curl $publicUrl/health

Frontend integration:
const API_BASE_URL = '$publicUrl/api/v1';

⏰ Valid for 2 hours
"@ -ForegroundColor White
        Write-Host "-" * 40 -ForegroundColor $Yellow

        # Open in browser
        Write-Host "`n🌐 Opening documentation in browser..." -ForegroundColor $Cyan
        Start-Process "$publicUrl/docs"
    } else {
        Write-Host "❌ Could not get ngrok URL" -ForegroundColor Red
        Write-Host "   Check ngrok output above" -ForegroundColor $Yellow
    }
} catch {
    Write-Host "❌ Could not connect to ngrok API" -ForegroundColor Red
    Write-Host "   Check if ngrok started properly" -ForegroundColor $Yellow
}

Write-Host "`n⏳ Keep this window open." -ForegroundColor $Yellow
Write-Host "   Press Ctrl+C to stop ngrok" -ForegroundColor $Yellow
Write-Host "=" * 60 -ForegroundColor $Cyan

# Keep script running
try {
    Wait-Process -Id $ngrokProcess.Id
} catch {
    # User pressed Ctrl+C
    Write-Host "`n👋 Stopped" -ForegroundColor $Green
}