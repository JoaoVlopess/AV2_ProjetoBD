$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

& "$ProjectRoot\venv\Scripts\python.exe" -m pip install -r "$ProjectRoot\backend\requirements.txt"

Push-Location "$ProjectRoot\frontend"
try {
    npm install
}
finally {
    Pop-Location
}
