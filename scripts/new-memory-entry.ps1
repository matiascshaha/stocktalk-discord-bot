param(
  [Parameter(Mandatory = $true)]
  [string]$Area,

  [Parameter(Mandatory = $true)]
  [ValidateSet("fact", "decision", "gotcha", "command")]
  [string]$Type,

  [Parameter(Mandatory = $true)]
  [string]$Summary,

  [Parameter(Mandatory = $true)]
  [string]$Evidence,

  [Parameter(Mandatory = $true)]
  [string]$Owner,

  [Parameter(Mandatory = $true)]
  [string]$ReviewDate
)

$ErrorActionPreference = "Stop"

$today = Get-Date -Format "yyyy-MM-dd"
$line = "| $today | $Area | $Type | $Summary | $Evidence | $Owner | $ReviewDate |"
Add-Content -Path "docs/ai-memory.md" -Value $line
Write-Host "Added memory entry to docs/ai-memory.md"
