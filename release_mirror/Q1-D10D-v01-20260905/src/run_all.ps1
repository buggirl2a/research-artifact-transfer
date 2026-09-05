$ErrorActionPreference = 'Stop'

$Root = 'C:\range_paper'
$Src = Join-Path $Root '06_src\d10d'
$Tmp = Join-Path $Root '99_tmp\d10d'
$NodeExe = 'C:\Users\bug_g\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$NodeModules = 'C:\Users\bug_g\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
$Junction = Join-Path $Tmp 'node_modules'

New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
if (-not (Test-Path -LiteralPath $Junction)) {
    New-Item -ItemType Junction -Path $Junction -Target $NodeModules | Out-Null
}

python (Join-Path $Src 'build.py')
if ($LASTEXITCODE -ne 0) { throw 'D10D build failed' }

Push-Location $Tmp
try {
    & $NodeExe (Join-Path $Src 'audit.mjs')
    if ($LASTEXITCODE -ne 0) { throw 'D10D workbook build/validation failed' }
}
finally {
    Pop-Location
}

python (Join-Path $Src 'verify.py')
if ($LASTEXITCODE -ne 0) { throw 'D10D independent validation failed' }

python (Join-Path $Src 'finalize.py')
if ($LASTEXITCODE -ne 0) { throw 'D10D finalization failed' }

