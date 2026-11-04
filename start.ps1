[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$CliPath = Join-Path $ScriptDir ".venv\Scripts\gitcraft-cli.exe"
if (Test-Path $CliPath) {
    & $CliPath @Args
} else {
    & uv run gitcraft-cli @Args
}
