param(
  [Parameter(Mandatory = $false)]
  [string]$Query,

  [Parameter(Mandatory = $false)]
  [int]$MaxMatches = 25
)

$ErrorActionPreference = "Stop"

Write-Host "== Agent Context Pack =="

if ($Query) {
  Write-Host "Query: $Query"
}

Write-Host "`n-- Core docs --"
$coreDocs = @(
  "AGENTS.md",
  "docs/architecture.md",
  "docs/conventions.md",
  "docs/testing.md",
  "docs/runbook.md",
  "docs/ai-memory.md"
)

foreach ($doc in $coreDocs) {
  if (Test-Path $doc) {
    Write-Host $doc
  }
}

Write-Host "`n-- Recently changed files (if git repo) --"
if (Test-Path ".git") {
  git status --short
} else {
  Write-Host "No git repository detected."
}

if ($Query) {
  Write-Host "`n-- Content matches --"
  if (Get-Command rg -ErrorAction SilentlyContinue) {
    rg --line-number --no-heading --max-count $MaxMatches $Query .
  } else {
    Get-ChildItem -Recurse -File | Select-String -Pattern $Query | Select-Object -First $MaxMatches
  }
}

Write-Host "`nTip: feed the output file paths and key lines into your next AI task prompt."
