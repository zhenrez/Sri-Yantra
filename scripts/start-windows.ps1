[CmdletBinding()]
param([int]$PreferredPort = 8765)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root '.venv'
$VenvPython = Join-Path $Venv 'Scripts\python.exe'
$Requirements = Join-Path $Root 'requirements.txt'

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Select-BasePython {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($selector in @('-3.13', '-3.11')) {
            $version = & $launcher.Source $selector -c "import platform; print(platform.python_version())" 2>$null
            if ($LASTEXITCODE -eq 0 -and $version -match '^(3\.13|3\.11)\.') {
                return @{ Command = $launcher.Source; Prefix = @($selector); Version = $version.Trim() }
            }
        }
    }

    # Controlled fallback: accept only a normal CPython 3.13/3.11 executable and
    # reject interpreters whose path advertises Conda, NVIDIA, CUDA, or an env.
    foreach ($candidate in @(Get-Command python.exe -All -ErrorAction SilentlyContinue)) {
        if ($candidate.Source -match '(?i)(conda|anaconda|miniconda|nvidia|cuda|\\envs?\\|\\\.venv\\)') { continue }
        $version = & $candidate.Source -c "import platform; print(platform.python_version())" 2>$null
        if ($LASTEXITCODE -eq 0 -and $version -match '^(3\.13|3\.11)\.') {
            return @{ Command = $candidate.Source; Prefix = @(); Version = $version.Trim() }
        }
    }

    throw @"
No isolated CPython 3.13 or 3.11 installation was found.

Install the official 64-bit build from python.org with the Python Launcher
enabled, then double-click START-SRI-WORKBENCH.cmd again. NVIDIA/Conda Python
installations are deliberately not used.
"@
}

function Get-OpenPort([int]$Start) {
    foreach ($port in $Start..($Start + 20)) {
        $listener = [System.Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $port)
        try { $listener.Start(); return $port } catch { } finally { $listener.Stop() }
    }
    throw "No open localhost port was found between $Start and $($Start + 20)."
}

try {
    Set-Location $Root
    Write-Step 'Selecting a clean CPython 3.13 or 3.11 installation'
    $Base = Select-BasePython
    Write-Host "Using CPython $($Base.Version): $($Base.Command) $($Base.Prefix -join ' ')"

    if (Test-Path $VenvPython) {
        $VenvInfo = & $VenvPython -I -c "import json,platform,sys; print(json.dumps({'version':platform.python_version(),'base':sys._base_executable}))" 2>$null
        $VenvAcceptable = $LASTEXITCODE -eq 0
        if ($VenvAcceptable) {
            try { $VenvInfo = $VenvInfo | ConvertFrom-Json } catch { $VenvAcceptable = $false }
        }
        if ($VenvAcceptable) {
            $VenvAcceptable = ($VenvInfo.version -match '^(3\.13|3\.11)\.') -and
                ($VenvInfo.base -notmatch '(?i)(conda|anaconda|miniconda|nvidia|cuda|\\envs?\\)')
        }
        if (-not $VenvAcceptable) {
            Write-Step 'Replacing an incompatible or externally managed virtual environment'
            Remove-Item -LiteralPath $Venv -Recurse -Force
        }
    }

    if (-not (Test-Path $VenvPython)) {
        Write-Step 'Creating the isolated virtual environment'
        $CreateArgs = @($Base.Prefix) + @('-m', 'venv', $Venv)
        & $Base.Command @CreateArgs
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPython)) {
            throw 'Virtual-environment creation failed.'
        }
    }

    # Isolation is process-local. Nothing is removed from Windows or from the
    # NVIDIA/Conda installations. Children see only the venv and core Windows.
    Get-ChildItem Env: | Where-Object {
        $_.Name -match '^(PYTHON|CONDA|_CONDA|VIRTUAL_ENV|PIPENV|POETRY|UV_|CUDA|NVIDIA)'
    } | ForEach-Object { Remove-Item "Env:$($_.Name)" -ErrorAction SilentlyContinue }

    $WindowsPaths = @(
        (Join-Path $env:SystemRoot 'System32'),
        $env:SystemRoot,
        (Join-Path $env:SystemRoot 'System32\Wbem'),
        (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0')
    )
    $env:VIRTUAL_ENV = $Venv
    $env:PYTHONNOUSERSITE = '1'
    $env:PYTHONPATH = ''
    $VenvScripts = Join-Path $Venv 'Scripts'
    $env:PATH = (@($VenvScripts) + $WindowsPaths) -join ';'

    Write-Step 'Installing the pinned project requirements'
    & $VenvPython -I -m pip install --disable-pip-version-check -r $Requirements
    if ($LASTEXITCODE -ne 0) { throw 'Requirement installation failed.' }

    Write-Step 'Rebuilding and verifying the sealed native dataset'
    $ExpectedSeal = (Get-Content (Join-Path $Root 'preregistration\sri-native-seal-v1.json') -Raw | ConvertFrom-Json).manifest_sha256
    & $VenvPython -I (Join-Path $Root 'compile_geometry.py')
    if ($LASTEXITCODE -ne 0) { throw 'Geometry compilation failed.' }
    & $VenvPython -I (Join-Path $Root 'seal_native.py')
    if ($LASTEXITCODE -ne 0) { throw 'Native-data sealing failed.' }
    $ActualSeal = (Get-Content (Join-Path $Root 'preregistration\sri-native-seal-v1.json') -Raw | ConvertFrom-Json).manifest_sha256
    if ($ActualSeal -ne $ExpectedSeal) {
        throw "Seal mismatch. Expected $ExpectedSeal but rebuilt $ActualSeal. The server was not launched."
    }

    $Port = Get-OpenPort $PreferredPort
    $Url = "http://127.0.0.1:$Port/"
    Write-Step "Launching the workbench at $Url"
    $Server = Start-Process -FilePath $VenvPython -ArgumentList @('-I', 'server.py', '--port', "$Port") -WorkingDirectory $Root -NoNewWindow -PassThru

    $Ready = $false
    for ($attempt = 0; $attempt -lt 50; $attempt++) {
        if ($Server.HasExited) { throw "The server stopped during startup with exit code $($Server.ExitCode)." }
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 1
            if ($response.StatusCode -eq 200) { $Ready = $true; break }
        } catch { Start-Sleep -Milliseconds 100 }
    }
    if (-not $Ready) { throw 'The server did not become ready within five seconds.' }

    Start-Process $Url
    Write-Host "`nWorkbench running. Keep this window open; press Ctrl+C to stop." -ForegroundColor Green
    try { Wait-Process -Id $Server.Id } finally {
        if (-not $Server.HasExited) { Stop-Process -Id $Server.Id -Force }
    }
}
catch {
    Write-Host "`nSTARTUP FAILED" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`nNo global Python, NVIDIA, CUDA, or Conda settings were changed."
    exit 1
}
