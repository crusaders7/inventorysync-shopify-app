# InventorySync Development Start Script for Windows
Write-Host "🚀 Starting InventorySync Development Environment..." -ForegroundColor Green

# Start Backend in a new PowerShell window
Write-Host "Starting Backend API on http://localhost:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd \\wsl$\Ubuntu\home\brend\inventorysync-shopify-app\backend; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start Frontend in a new PowerShell window
Write-Host "Starting Frontend on http://localhost:5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd \\wsl$\Ubuntu\home\brend\inventorysync-shopify-app\frontend; npm run dev"

Write-Host "`n✅ Development servers starting up!" -ForegroundColor Green
Write-Host "-----------------------------------" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C in each window to stop the servers" -ForegroundColor Yellow
