# Mandatory install step (Windows, PowerShell): Ollama + qwen2.5:1.5b.
#
#   powershell -ExecutionPolicy Bypass -File scripts/setup-ollama.ps1
#
# Same steps as the bash version: install Ollama (if missing), start the server,
# pull the model, verify it actually answers. Every step is idempotent.
#
# NOTE: messages are intentionally ASCII-only - Windows PowerShell 5.1 misreads
# UTF-8 scripts without a BOM and mangles non-ASCII output in the console.
$ErrorActionPreference = "Stop"

$Model      = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "qwen2.5:1.5b" }
$OllamaPort = 11434

function Log($msg)  { Write-Host "[ollama] $msg" -ForegroundColor Cyan }
function Ok($msg)  { Write-Host "  OK  $msg" -ForegroundColor Green }
function Die($msg) { Write-Host "  FAIL $msg" -ForegroundColor Red; exit 1 }

# --- 1. Find or install Ollama -----------------------------------------------

function Find-Ollama {
    if (Get-Command ollama -ErrorAction SilentlyContinue) {
        return (Get-Command ollama).Source
    }
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
        "$env:ProgramFiles\Ollama\ollama.exe"
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }
    return $null
}

$ollama = Find-Ollama

if (-not $ollama) {
    Log "Ollama not found - installing..."
    $installer = Join-Path $env:TEMP "OllamaSetup.exe"
    Log "Downloading https://ollama.com/download/OllamaSetup.exe"
    try {
        Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $installer -UseBasicParsing
        Start-Process -FilePath $installer -ArgumentList "/S" -Wait
        Log "Installer finished"
    } catch {
        Die "Could not download/run the Ollama installer. Install it manually from https://ollama.com/download/"
    }

    $ollama = Find-Ollama
    if (-not $ollama) {
        Die "Ollama installed but ollama.exe not found in PATH. Restart the terminal and retry."
    }
}
Ok "Ollama found: $ollama"
& $ollama --version 2>$null | Select-Object -First 1

# --- 2. Start the Ollama server ----------------------------------------------

function Test-Server {
    try {
        Invoke-RestMethod -Uri "http://localhost:$OllamaPort/api/tags" -TimeoutSec 10 | Out-Null
        return $true
    } catch { return $false }
}

if (Test-Server) {
    Ok "Ollama server already responding on port $OllamaPort"
} else {
    Log "Starting the Ollama server in the background..."
    Start-Process -FilePath $ollama -ArgumentList "serve" -WindowStyle Hidden
    for ($i = 0; $i -lt 30; $i++) {
        if (Test-Server) { break }
        Start-Sleep -Seconds 1
    }
    if (Test-Server) { Ok "Ollama server is up on port $OllamaPort" }
    else { Die "Ollama server did not start. Run it manually: & $ollama serve" }
}

# --- 3. Pull the model --------------------------------------------------------

$tags = Invoke-RestMethod -Uri "http://localhost:$OllamaPort/api/tags" -TimeoutSec 10
$already = $tags.models | Where-Object { $_.name -eq $Model -or $_.model -eq $Model }

if ($already) {
    Ok "Model $Model is already downloaded"
} else {
    Log "Pulling model $Model (~1 GB, one-time download)..."
    & $ollama pull $Model
    if ($LASTEXITCODE -ne 0) { Die "Could not pull model $Model" }
    Ok "Model $Model downloaded"
}

# --- 4. Verify the model actually answers ------------------------------------

Log "Checking inference..."
$body = @{
    model    = $Model
    messages = @(@{ role = "user"; content = "Say OK" })
    stream   = $false
} | ConvertTo-Json -Depth 5

try {
    $resp = Invoke-RestMethod -Uri "http://localhost:$OllamaPort/api/chat" -Method Post `
        -Body $body -ContentType "application/json" -TimeoutSec 180
} catch {
    Die "Chat request failed: $_"
}

if (-not $resp.message.content) {
    Die "The model returned no text. Check manually: ollama run $Model `"Say OK`""
}

Ok "Model responds: $($resp.message.content)"

Write-Host ""
Write-Host "Ollama is ready. Model: $Model, endpoint: http://localhost:$OllamaPort" -ForegroundColor Green
Write-Host "Check manually:  curl http://localhost:$OllamaPort/api/tags"
