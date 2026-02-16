param(
  [switch]$Fast
)

$ErrorActionPreference = "Stop"

function Run-Step {
  param(
    [string]$Name,
    [string]$Command
  )

  Write-Host "`n== $Name =="
  Write-Host $Command
  iex $Command
}

Write-Host "Running validation workflow..."

# Replace these placeholders in your repo.
$lintCmd = "<LINT_COMMAND>"
$typecheckCmd = "<TYPECHECK_COMMAND>"
$unitCmd = "<UNIT_TEST_COMMAND>"
$integrationCmd = "<INTEGRATION_TEST_COMMAND>"
$e2eCmd = "<E2E_COMMAND>"

if ($lintCmd -notmatch "^<") { Run-Step -Name "Lint" -Command $lintCmd }
if ($typecheckCmd -notmatch "^<") { Run-Step -Name "Typecheck" -Command $typecheckCmd }
if ($unitCmd -notmatch "^<") { Run-Step -Name "Unit tests" -Command $unitCmd }

if (-not $Fast) {
  if ($integrationCmd -notmatch "^<") { Run-Step -Name "Integration tests" -Command $integrationCmd }
  if ($e2eCmd -notmatch "^<") { Run-Step -Name "E2E tests" -Command $e2eCmd }
}

Write-Host "`nValidation flow completed."
