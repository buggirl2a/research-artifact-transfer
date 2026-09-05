$ErrorActionPreference = 'Stop'

$RangeRoot = 'C:\range_paper'
$D10ESource = Join-Path $RangeRoot '06_src\d10e'
$D10ETemp = Join-Path $RangeRoot '99_tmp\d10e'
$BundledPython = 'C:\Users\bug_g\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$FigurePython = 'C:\Python\Python312\python.exe'
$NodeExe = 'C:\Users\bug_g\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$NodeModules = 'C:\Users\bug_g\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
$Junction = Join-Path $D10ETemp 'node_modules'

New-Item -ItemType Directory -Force -Path $D10ETemp | Out-Null
if (-not (Test-Path -LiteralPath $Junction)) {
    New-Item -ItemType Junction -Path $Junction -Target $NodeModules | Out-Null
}

& $BundledPython (Join-Path $D10ESource 'build.py')
if ($LASTEXITCODE -ne 0) { throw 'D10E computation failed' }

& $BundledPython (Join-Path $D10ESource 'verify.py')
if ($LASTEXITCODE -ne 0) { throw 'D10E independent validation failed' }

& $FigurePython (Join-Path $D10ESource 'figures.py')
if ($LASTEXITCODE -ne 0) { throw 'D10E figure generation failed' }

Push-Location (Join-Path $D10ETemp 'xlsx_builder')
try {
    & $NodeExe (Join-Path $D10ESource 'audit.mjs')
    if ($LASTEXITCODE -ne 0) { throw 'D10E workbook build or validation failed' }
}
finally {
    Pop-Location
}

& $BundledPython (Join-Path $D10ESource 'finalize.py')
if ($LASTEXITCODE -ne 0) { throw 'D10E package finalization failed' }
