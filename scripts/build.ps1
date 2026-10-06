$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Push-Location "$ProjectRoot\frontend"
try {
    npm run build
}
finally {
    Pop-Location
}
