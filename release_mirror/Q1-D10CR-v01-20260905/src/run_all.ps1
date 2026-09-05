$ErrorActionPreference = 'Stop'
$src = 'C:\range_paper\06_src\d10cr'
$tmp = 'C:\range_paper\99_tmp\d10cr'
$node = 'C:\Users\bug_g\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$modules = 'C:\Users\bug_g\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'

New-Item -ItemType Directory -Path $tmp -Force | Out-Null
$link = Join-Path $tmp 'node_modules'
if (-not (Test-Path -LiteralPath $link)) {
    New-Item -ItemType Junction -Path $link -Target $modules | Out-Null
}

python (Join-Path $src 'build.py')
Push-Location $tmp
try {
    & $node (Join-Path $src 'audit.mjs')
    & $node (Join-Path $src 'verify_xlsx.mjs')
} finally {
    Pop-Location
}
python (Join-Path $src 'finalize.py')
