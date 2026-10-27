# Run every test suite (Windows PowerShell, from the repository root, venv activated)
$ErrorActionPreference = "Stop"
Push-Location ml;       python -m pytest -q; Pop-Location
Push-Location backend;  python -m pytest -q; Pop-Location
Push-Location frontend; npm test; npm run build; Pop-Location
Write-Host "All suites finished"
