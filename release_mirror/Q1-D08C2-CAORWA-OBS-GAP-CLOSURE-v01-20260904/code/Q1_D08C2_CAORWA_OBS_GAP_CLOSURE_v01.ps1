# Q1 / corrected D08C2 — CA/OR/WA observational-data gap closure v01
# TASK_ID: D08C2_CAORWA_OBSERVATIONAL_GAP_CLOSURE_v01
# Data Search Line only. Acquisition + species-blind structural verification.
# Explicitly forbidden here: D08C2 execution, species eligibility, species survivor counts,
# abundance/support/occupancy/detection/Q1 outcomes, F0 redesign, national SQLite, Little, GBIF.

[CmdletBinding()]
param(
    [string]$ObsRoot = "C:\range_paper\02_raw\fia_t2_2023_observational_gap_v01",
    [string]$DesignRoot = "C:\range_paper\02_raw\fia_t2_2023_raw_design_v01",
    [int]$MaxRetries = 4,
    [int]$RetryDelaySeconds = 8,
    [int]$TimeoutMinutes = 720
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
Add-Type -AssemblyName System.Net.Http
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName Microsoft.VisualBasic

$TaskId = 'D08C2_CAORWA_OBSERVATIONAL_GAP_CLOSURE_v01'
$RunId = ([Guid]::NewGuid().ToString('N')).Substring(0,12)
$RunStart = Get-Date
$RunStamp = $RunStart.ToString('yyyyMMddTHHmmss')

$RawDir = Join-Path $ObsRoot 'raw_table_zips'
$HeaderDir = Join-Path $ObsRoot 'http_headers'
$ManifestDir = Join-Path $ObsRoot 'manifests'
$OutputDir = Join-Path $ObsRoot 'outputs'
$QcDir = Join-Path $ObsRoot 'qc'
$LogDir = Join-Path $ObsRoot 'logs'
$FailedDir = Join-Path $LogDir 'failed_responses'
$WorkingDir = Join-Path $ObsRoot ("working\run_{0}_{1}" -f $RunStamp,$RunId)
$RelayRoot = Join-Path $ObsRoot ("relay_payload_v01\run_{0}_{1}" -f $RunStamp,$RunId)
foreach ($d in @($ObsRoot,$RawDir,$HeaderDir,$ManifestDir,$OutputDir,$QcDir,$LogDir,$FailedDir,$WorkingDir,$RelayRoot)) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

$LogPath = Join-Path $LogDir ("D08C2_CAORWA_OBS_GAP_CLOSURE_{0}_{1}.log" -f $RunStamp,$RunId)
$RawManifestPath = Join-Path $ManifestDir 'Q1_D08C2_CAORWA_OBS_RAW_ASSET_MANIFEST_v01.csv'
$DownloadStatusPath = Join-Path $ManifestDir 'Q1_D08C2_CAORWA_OBS_DOWNLOAD_STATUS_v01.csv'
$LinkagePath = Join-Path $OutputDir 'Q1_D08C2_CAORWA_OBS_F0_LINKAGE_CHECK_v01.csv'
$SchemaPath = Join-Path $OutputDir 'Q1_D08C2_CAORWA_OBS_SCHEMA_CHECK_v01.csv'
$QcPath = Join-Path $QcDir 'Q1_D08C2_CAORWA_OBS_GAP_CLOSURE_QC_v01.csv'
$ResultNotePath = Join-Path $OutputDir 'Q1_D08C2_CAORWA_OBS_RESULT_NOTE_v01.md'
$ShaPath = Join-Path $ManifestDir 'SHA256SUMS.csv'
$RegistryDeltaPath = Join-Path $ManifestDir 'REGISTRY_DELTA_v01.csv'
$TransferManifestPath = Join-Path $RelayRoot 'TRANSFER_MANIFEST_v01.csv'

function Write-Log {
    param([string]$Message,[string]$Level='INFO')
    $line = "{0} [{1}] [{2}] {3}" -f (Get-Date).ToString('o'),$Level,$RunId,$Message
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
    Write-Host $line
}
function Get-SafeString { param($Value) if ($null -eq $Value) { return '' } return [string]$Value }
trap {
    $err=$_.Exception.Message
    $pos=Get-SafeString $_.InvocationInfo.PositionMessage
    try { Write-Log ("RUNTIME ERROR: {0} :: {1}" -f $err,$pos) 'ERROR' } catch {}
    Write-Host ''
    Write-Host 'FINAL_STATUS = INPUT_BLOCKED_INTEGRITY_OR_SCHEMA_FAILURE'
    Write-Host ("ERROR = {0}" -f $err)
    if ($pos) { Write-Host $pos }
    Write-Host ("LOG = {0}" -f $LogPath)
    Write-Host 'STOP: corrected D08C2 was NOT run.'
    exit 4
}
function Get-Sha256Lower { param([string]$Path) return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant() }
function Get-FileBytes { param([string]$Path) return (Get-Item -LiteralPath $Path).Length }
function Safe-Name { param([string]$Text) return ($Text -replace '[^A-Za-z0-9._-]','_') }
function Get-Field {
    param($Row,[string[]]$Names)
    if ($null -eq $Row) { return '' }
    foreach ($n in $Names) {
        foreach ($p in $Row.PSObject.Properties) {
            if ($p.Name -ieq $n) { return (Get-SafeString $p.Value) }
        }
    }
    return ''
}
function Write-AllLinesUtf8NoBom {
    param([string]$Path,[string[]]$Lines)
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($Path,$Lines,$enc)
}
function Get-HttpHeaderValue {
    param([Parameter(Mandatory=$true)]$Headers,[Parameter(Mandatory=$true)][string]$Name)
    try {
        $values = @($Headers.GetValues($Name))
        if ($values.Count -gt 0) { return [string]::Join(', ',[string[]]$values) }
    } catch {}
    return ''
}
function Format-ResponseHeaders {
    param([System.Net.Http.HttpResponseMessage]$Response,[string]$OriginalUrl,[string]$RetrievedUtc,[string]$RetrievedLocal)
    $lines = New-Object 'System.Collections.Generic.List[string]'
    [void]$lines.Add(("HTTP/{0} {1} {2}" -f $Response.Version.ToString(),[int]$Response.StatusCode,$Response.ReasonPhrase))
    [void]$lines.Add("Request-URL: $OriginalUrl")
    [void]$lines.Add("Final-URL: $($Response.RequestMessage.RequestUri.AbsoluteUri)")
    [void]$lines.Add("Retrieved-At-UTC: $RetrievedUtc")
    [void]$lines.Add("Retrieved-At-Local: $RetrievedLocal")
    $a = $Response.Headers.ToString()
    if ($a) { foreach ($line in ($a -split "`r?`n")) { if ($line) { [void]$lines.Add($line) } } }
    $b = $Response.Content.Headers.ToString()
    if ($b) { foreach ($line in ($b -split "`r?`n")) { if ($line) { [void]$lines.Add($line) } } }
    return [string[]]$lines
}
function Invoke-OneHttpAttempt {
    param([string]$Url,[string]$TempBody,[string]$TempHeaders,[int]$TimeoutMinutes)
    $handler=$null; $client=$null; $request=$null; $response=$null; $stream=$null; $fs=$null
    try {
        $handler = New-Object System.Net.Http.HttpClientHandler
        $handler.AllowAutoRedirect = $true
        $handler.AutomaticDecompression = [System.Net.DecompressionMethods]::None
        $client = New-Object System.Net.Http.HttpClient -ArgumentList $handler
        $client.Timeout = [TimeSpan]::FromMinutes($TimeoutMinutes)
        $client.DefaultRequestHeaders.UserAgent.ParseAdd('Q1-D08C2-CAORWA-observational-gap-closure-v01/1.0')
        $request = New-Object System.Net.Http.HttpRequestMessage -ArgumentList ([System.Net.Http.HttpMethod]::Get,$Url)
        [void]$request.Headers.TryAddWithoutValidation('Accept-Encoding','identity')
        $response = $client.SendAsync($request,[System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
        $retrievedLocal = (Get-Date).ToString('o')
        $retrievedUtc = (Get-Date).ToUniversalTime().ToString('o')
        Write-AllLinesUtf8NoBom -Path $TempHeaders -Lines (Format-ResponseHeaders -Response $response -OriginalUrl $Url -RetrievedUtc $retrievedUtc -RetrievedLocal $retrievedLocal)
        $stream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
        $fs = [System.IO.File]::Open($TempBody,[System.IO.FileMode]::Create,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
        $buffer=New-Object byte[] (1024*1024)
        [Int64]$total=0; [Int64]$nextProgress=128MB
        while (($n=$stream.Read($buffer,0,$buffer.Length)) -gt 0) {
            $fs.Write($buffer,0,$n); $total += $n
            if ($total -ge $nextProgress) { Write-Log ("HTTP body progress: {0:N1} MiB :: {1}" -f ($total/1MB),$Url); $nextProgress += 128MB }
        }
        $fs.Flush(); $fs.Dispose(); $fs=$null; $stream.Dispose(); $stream=$null
        return [pscustomobject]@{
            TransportSuccess=$true; HttpStatus=[int]$response.StatusCode; HttpSuccess=$response.IsSuccessStatusCode;
            FinalUrl=$response.RequestMessage.RequestUri.AbsoluteUri;
            ContentType=(Get-HttpHeaderValue -Headers $response.Content.Headers -Name 'Content-Type');
            ContentLength=(Get-HttpHeaderValue -Headers $response.Content.Headers -Name 'Content-Length');
            ETag=(Get-HttpHeaderValue -Headers $response.Headers -Name 'ETag');
            LastModified=(Get-HttpHeaderValue -Headers $response.Content.Headers -Name 'Last-Modified');
            RetrievedAtUtc=$retrievedUtc; RetrievedAtLocal=$retrievedLocal; ErrorMessage=''
        }
    } catch {
        return [pscustomobject]@{TransportSuccess=$false;HttpStatus='';HttpSuccess=$false;FinalUrl='';ContentType='';ContentLength='';ETag='';LastModified='';RetrievedAtUtc=(Get-Date).ToUniversalTime().ToString('o');RetrievedAtLocal=(Get-Date).ToString('o');ErrorMessage=$_.Exception.Message}
    } finally {
        if ($null -ne $fs) { $fs.Dispose() }; if ($null -ne $stream) { $stream.Dispose() }; if ($null -ne $response) { $response.Dispose() }; if ($null -ne $request) { $request.Dispose() }; if ($null -ne $client) { $client.Dispose() }; if ($null -ne $handler) { $handler.Dispose() }
    }
}
function Invoke-HttpWithRetry {
    param([string]$Url,[string]$TempBody,[string]$TempHeaders,[int]$MaxRetries,[int]$RetryDelaySeconds,[int]$TimeoutMinutes)
    $last=$null
    for ($attempt=1; $attempt -le $MaxRetries; $attempt++) {
        Remove-Item -LiteralPath $TempBody -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $TempHeaders -Force -ErrorAction SilentlyContinue
        Write-Log ("GET attempt {0}/{1}: {2}" -f $attempt,$MaxRetries,$Url)
        $last = Invoke-OneHttpAttempt -Url $Url -TempBody $TempBody -TempHeaders $TempHeaders -TimeoutMinutes $TimeoutMinutes
        $last | Add-Member -NotePropertyName Attempts -NotePropertyValue $attempt -Force
        if ($last.TransportSuccess -and $last.HttpSuccess) { return $last }
        if ($last.TransportSuccess) {
            $code=[int]$last.HttpStatus
            if ($code -in @(400,401,403,404,410)) { return $last }
            if (-not ($code -eq 408 -or $code -eq 429 -or $code -ge 500)) { return $last }
        }
        if ($attempt -lt $MaxRetries) {
            $delay=[int]($RetryDelaySeconds * [Math]::Pow(2,($attempt-1)))
            Write-Log ("Retrying after {0}s. Last status/error: {1} {2}" -f $delay,$last.HttpStatus,$last.ErrorMessage) 'WARN'
            Start-Sleep -Seconds $delay
        }
    }
    return $last
}
function Test-ZipExpectedMember {
    param([string]$Path,[string]$ExpectedMember)
    $zip=$null
    try {
        $zip=[System.IO.Compression.ZipFile]::OpenRead($Path)
        $entries=@($zip.Entries)
        $found=$false
        foreach ($e in $entries) { if ($e.Name -ieq $ExpectedMember) { $found=$true; break } }
        return [pscustomobject]@{Valid=($entries.Count -gt 0 -and $found);EntryCount=$entries.Count;ExpectedPresent=$found;Message=$(if ($found) {'ZIP readable; expected member present.'} else {"Expected member absent: $ExpectedMember"})}
    } catch { return [pscustomobject]@{Valid=$false;EntryCount=0;ExpectedPresent=$false;Message=$_.Exception.Message} }
    finally { if ($null -ne $zip) { $zip.Dispose() } }
}
function Extract-ZipMemberReadOnlyCopy {
    param([string]$ZipPath,[string]$ExpectedMember,[string]$Destination)
    $zip=$null; $src=$null; $dst=$null
    try {
        $zip=[System.IO.Compression.ZipFile]::OpenRead($ZipPath)
        $entry=$null
        foreach ($e in $zip.Entries) { if ($e.Name -ieq $ExpectedMember) { $entry=$e; break } }
        if ($null -eq $entry) { throw "Expected member not found: $ExpectedMember" }
        $parent=Split-Path -Parent $Destination
        if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        $src=$entry.Open()
        $dst=[System.IO.File]::Open($Destination,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
        $src.CopyTo($dst); $dst.Flush()
    } finally { if ($null -ne $dst) {$dst.Dispose()}; if ($null -ne $src) {$src.Dispose()}; if ($null -ne $zip) {$zip.Dispose()} }
}
function Get-CsvHeader {
    param([string]$Path)
    $p=$null
    try {
        $p=New-Object Microsoft.VisualBasic.FileIO.TextFieldParser -ArgumentList $Path
        $p.TextFieldType=[Microsoft.VisualBasic.FileIO.FieldType]::Delimited
        $p.SetDelimiters([string[]]@(',')); $p.HasFieldsEnclosedInQuotes=$true; $p.TrimWhiteSpace=$false
        if ($p.EndOfData) { return @() }
        return [string[]]$p.ReadFields()
    } finally { if ($null -ne $p) { $p.Close() } }
}
function New-HeaderMap {
    param([string[]]$Header)
    $m=@{}
    for ($i=0; $i -lt $Header.Count; $i++) { $m[([string]$Header[$i]).ToUpperInvariant()]=$i }
    return $m
}
function Test-Columns {
    param([string[]]$Header,[string[]]$Required)
    $set=@{}; foreach ($h in $Header) { $set[([string]$h).ToUpperInvariant()]=$true }
    $missing=New-Object System.Collections.ArrayList
    foreach ($r in $Required) { if (-not $set.ContainsKey(([string]$r).ToUpperInvariant())) { [void]$missing.Add($r) } }
    return [pscustomobject]@{Pass=($missing.Count -eq 0);Missing=([string]::Join(';',[string[]]@($missing)))}
}
function Stream-PlotTable {
    param([string]$Path)
    $parser=$null
    try {
        $parser=New-Object Microsoft.VisualBasic.FileIO.TextFieldParser -ArgumentList $Path
        $parser.TextFieldType=[Microsoft.VisualBasic.FileIO.FieldType]::Delimited; $parser.SetDelimiters([string[]]@(',')); $parser.HasFieldsEnclosedInQuotes=$true; $parser.TrimWhiteSpace=$false
        if ($parser.EndOfData) { throw 'PLOT CSV empty.' }
        $header=[string[]]$parser.ReadFields(); $map=New-HeaderMap $header
        foreach ($req in @('CN','STATECD','INVYR')) { if (-not $map.ContainsKey($req)) { throw "PLOT missing required field $req" } }
        $plots=@{}; $rowCount=0
        while (-not $parser.EndOfData) {
            $f=$parser.ReadFields(); if ($null -eq $f) { continue }; $rowCount++
            $cn=Get-SafeString $f[$map['CN']]
            if (-not $cn) { continue }
            $plots[$cn]=[pscustomobject]@{STATECD=(Get-SafeString $f[$map['STATECD']]);INVYR=(Get-SafeString $f[$map['INVYR']])}
        }
        return [pscustomobject]@{Plots=$plots;RowCount=$rowCount;Header=$header}
    } finally { if ($null -ne $parser) { $parser.Close() } }
}
function Stream-PpsaF0 {
    param([string]$Path,[string]$TargetEvalid)
    $parser=$null
    try {
        $parser=New-Object Microsoft.VisualBasic.FileIO.TextFieldParser -ArgumentList $Path
        $parser.TextFieldType=[Microsoft.VisualBasic.FileIO.FieldType]::Delimited; $parser.SetDelimiters([string[]]@(',')); $parser.HasFieldsEnclosedInQuotes=$true; $parser.TrimWhiteSpace=$false
        if ($parser.EndOfData) { throw 'POP_PLOT_STRATUM_ASSGN CSV empty.' }
        $header=[string[]]$parser.ReadFields(); $map=New-HeaderMap $header
        foreach ($req in @('EVALID','PLT_CN')) { if (-not $map.ContainsKey($req)) { throw "POP_PLOT_STRATUM_ASSGN missing required field $req" } }
        $f0=@{}; $rows=0
        while (-not $parser.EndOfData) {
            $f=$parser.ReadFields(); if ($null -eq $f) { continue }
            if ((Get-SafeString $f[$map['EVALID']]) -eq $TargetEvalid) {
                $rows++; $p=Get-SafeString $f[$map['PLT_CN']]; if ($p) { $f0[$p]=$true }
            }
        }
        return [pscustomobject]@{F0=$f0;MembershipRows=$rows;Header=$header}
    } finally { if ($null -ne $parser) { $parser.Close() } }
}
function Stream-ObsProfile {
    param([string]$Path,[string]$Table,[string]$ExpectedStateCd,[hashtable]$FrozenPlots,[hashtable]$F0Plots)
    $parser=$null
    try {
        $parser=New-Object Microsoft.VisualBasic.FileIO.TextFieldParser -ArgumentList $Path
        $parser.TextFieldType=[Microsoft.VisualBasic.FileIO.FieldType]::Delimited; $parser.SetDelimiters([string[]]@(',')); $parser.HasFieldsEnclosedInQuotes=$true; $parser.TrimWhiteSpace=$false
        if ($parser.EndOfData) { throw "$Table CSV empty." }
        $header=[string[]]$parser.ReadFields(); $map=New-HeaderMap $header
        foreach ($req in @('PLT_CN','STATECD','INVYR')) { if (-not $map.ContainsKey($req)) { throw "$Table missing linkage field $req" } }
        $rowCount=0; $rows2023=0; $wrongState=0; $f0Rows=0; $f0Rows2023=0; $minInv=$null; $maxInv=$null
        $f0Linked=@{}; $f0Linked2023=@{}; $orph2023=@{}
        while (-not $parser.EndOfData) {
            $f=$parser.ReadFields(); if ($null -eq $f) { continue }; $rowCount++
            $plt=Get-SafeString $f[$map['PLT_CN']]; $st=Get-SafeString $f[$map['STATECD']]; $inv=Get-SafeString $f[$map['INVYR']]
            if ($st -and $st -ne $ExpectedStateCd) { $wrongState++ }
            if ($inv -match '^[0-9]{4}$') { $iv=[int]$inv; if ($null -eq $minInv -or $iv -lt $minInv) {$minInv=$iv}; if ($null -eq $maxInv -or $iv -gt $maxInv) {$maxInv=$iv} }
            if ($inv -eq '2023') {
                $rows2023++
                if ($plt -and -not $FrozenPlots.ContainsKey($plt)) { $orph2023[$plt]=$true }
            }
            if ($plt -and $F0Plots.ContainsKey($plt)) {
                $f0Rows++; $f0Linked[$plt]=$true
                if ($inv -eq '2023') { $f0Rows2023++; $f0Linked2023[$plt]=$true }
            }
        }
        return [pscustomobject]@{Header=$header;RowCount=$rowCount;Rows2023=$rows2023;WrongStateRows=$wrongState;MinInvyr=(Get-SafeString $minInv);MaxInvyr=(Get-SafeString $maxInv);F0Rows=$f0Rows;F0Rows2023=$f0Rows2023;F0LinkedUnique=$f0Linked.Count;F0Linked2023Unique=$f0Linked2023.Count;Orphan2023Unique=$orph2023.Count}
    } finally { if ($null -ne $parser) { $parser.Close() } }
}
function Find-DesignManifestRow {
    param([object[]]$Rows,[string]$FileName)
    foreach ($r in $Rows) {
        $p=Get-Field $r @('LOCAL_PATH','LOCAL_FILE','ORIGINAL_LOCAL_PATH','PATH','FILE','FILE_PATH')
        $n=Get-Field $r @('FILE_NAME','FILENAME','ASSET','NAME')
        if ($p -and ([System.IO.Path]::GetFileName($p) -ieq $FileName)) { return $r }
        if ($n -and $n -ieq $FileName) { return $r }
    }
    return $null
}
function Export-CsvAtomic {
    param([object[]]$Rows,[string]$Path)
    $tmp="$Path.tmp.$RunId"
    $arr=@($Rows)
    if ($arr.Count -eq 0) {
        [System.IO.File]::WriteAllText($tmp,'',(New-Object System.Text.UTF8Encoding($false)))
    } else {
        $arr | Export-Csv -LiteralPath $tmp -NoTypeInformation -Encoding UTF8
    }
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Preserve-Failed {
    param([string]$Body,[string]$Headers,[string]$Label)
    $stamp=(Get-Date).ToString('yyyyMMddTHHmmssfff'); $safe=Safe-Name $Label
    if (Test-Path -LiteralPath $Body) { Move-Item -LiteralPath $Body -Destination (Join-Path $FailedDir ("{0}_{1}.body" -f $safe,$stamp)) }
    if (Test-Path -LiteralPath $Headers) { Move-Item -LiteralPath $Headers -Destination (Join-Path $FailedDir ("{0}_{1}.headers.txt" -f $safe,$stamp)) }
}

# Exact frozen acquisition plan: 3 states x 3 tables; no other endpoint is legal in this task.
$Plan=@(
    [pscustomobject]@{State='CA';StateName='California';StateCd='6';Table='TREE';Url='https://apps.fs.usda.gov/fia/datamart/CSV/CA_TREE.zip';FileName='CA_TREE.zip';ExpectedMember='CA_TREE.csv'},
    [pscustomobject]@{State='CA';StateName='California';StateCd='6';Table='COND';Url='https://apps.fs.usda.gov/fia/datamart/CSV/CA_COND.zip';FileName='CA_COND.zip';ExpectedMember='CA_COND.csv'},
    [pscustomobject]@{State='CA';StateName='California';StateCd='6';Table='SUBPLOT';Url='https://apps.fs.usda.gov/fia/datamart/CSV/CA_SUBPLOT.zip';FileName='CA_SUBPLOT.zip';ExpectedMember='CA_SUBPLOT.csv'},
    [pscustomobject]@{State='OR';StateName='Oregon';StateCd='41';Table='TREE';Url='https://apps.fs.usda.gov/fia/datamart/CSV/OR_TREE.zip';FileName='OR_TREE.zip';ExpectedMember='OR_TREE.csv'},
    [pscustomobject]@{State='OR';StateName='Oregon';StateCd='41';Table='COND';Url='https://apps.fs.usda.gov/fia/datamart/CSV/OR_COND.zip';FileName='OR_COND.zip';ExpectedMember='OR_COND.csv'},
    [pscustomobject]@{State='OR';StateName='Oregon';StateCd='41';Table='SUBPLOT';Url='https://apps.fs.usda.gov/fia/datamart/CSV/OR_SUBPLOT.zip';FileName='OR_SUBPLOT.zip';ExpectedMember='OR_SUBPLOT.csv'},
    [pscustomobject]@{State='WA';StateName='Washington';StateCd='53';Table='TREE';Url='https://apps.fs.usda.gov/fia/datamart/CSV/WA_TREE.zip';FileName='WA_TREE.zip';ExpectedMember='WA_TREE.csv'},
    [pscustomobject]@{State='WA';StateName='Washington';StateCd='53';Table='COND';Url='https://apps.fs.usda.gov/fia/datamart/CSV/WA_COND.zip';FileName='WA_COND.zip';ExpectedMember='WA_COND.csv'},
    [pscustomobject]@{State='WA';StateName='Washington';StateCd='53';Table='SUBPLOT';Url='https://apps.fs.usda.gov/fia/datamart/CSV/WA_SUBPLOT.zip';FileName='WA_SUBPLOT.zip';ExpectedMember='WA_SUBPLOT.csv'}
)
$F0=@{CA='62301';OR='412301';WA='532301'}
$RequiredColumns=@{
    TREE=@('CN','PLT_CN','STATECD','INVYR','SUBP','TREE','CONDID','STATUSCD','SPCD');
    COND=@('CN','PLT_CN','STATECD','INVYR','CONDID','COND_STATUS_CD');
    SUBPLOT=@('CN','PLT_CN','STATECD','INVYR','SUBP')
}

# Hard scope guard.
$allowedFiles=@('CA_TREE.zip','CA_COND.zip','CA_SUBPLOT.zip','OR_TREE.zip','OR_COND.zip','OR_SUBPLOT.zip','WA_TREE.zip','WA_COND.zip','WA_SUBPLOT.zip')
$bad=@($Plan | Where-Object { $_.FileName -notin $allowedFiles -or $_.Url -notlike 'https://apps.fs.usda.gov/fia/datamart/CSV/*.zip' })
if ($Plan.Count -ne 9 -or $bad.Count -gt 0) { throw 'Scope guard failed: acquisition plan is not exactly the nine authorized FIA state-table ZIPs.' }
Write-Log "BEGIN $TaskId. New observational root=$ObsRoot"
Write-Log 'Scope guard: nine FIA DataMart ZIPs only; no PLOT re-download; no national SQLite; no Little/GBIF; no D08C2/species analysis.'

$rawRows=New-Object System.Collections.ArrayList
$statusRows=New-Object System.Collections.ArrayList
$downloadUnavailable=$false; $integrityFailure=$false
$priorRaw=@{}
if (Test-Path -LiteralPath $RawManifestPath) {
    try { foreach ($r in (Import-Csv -LiteralPath $RawManifestPath)) { $k="$(Get-Field $r @('STATE'))|$(Get-Field $r @('TABLE'))"; if ($k -ne '|') {$priorRaw[$k]=$r} } } catch { Write-Log "Prior observational manifest unreadable; existing raw files will not be trusted without matching prior evidence. $($_.Exception.Message)" 'WARN' }
}

foreach ($item in $Plan) {
    $key="$($item.State)|$($item.Table)"; $target=Join-Path $RawDir $item.FileName; $headerPath=Join-Path $HeaderDir ("{0}_{1}.headers.txt" -f $item.State,$item.Table)
    Write-Log "RAW start $key -> $target"
    $reuse=$false
    if (Test-Path -LiteralPath $target) {
        if ($priorRaw.ContainsKey($key)) {
            $pr=$priorRaw[$key]; $expectedSha=(Get-Field $pr @('SHA256','BODY_SHA256')).ToLowerInvariant(); $actualSha=Get-Sha256Lower $target
            $zipTest=Test-ZipExpectedMember -Path $target -ExpectedMember $item.ExpectedMember
            if ($expectedSha -and $expectedSha -eq $actualSha -and $zipTest.Valid -and (Test-Path -LiteralPath $headerPath)) {
                $reuse=$true; Write-Log "Existing frozen asset verified and reused: $($item.FileName) sha256=$actualSha"
                [void]$rawRows.Add([pscustomobject]@{STATE=$item.State;TABLE=$item.Table;OFFICIAL_URL=$item.Url;FINAL_URL=(Get-Field $pr @('FINAL_URL'));LOCAL_PATH=$target;HEADERS_LOCAL_PATH=$headerPath;HEADERS_SHA256=(Get-Sha256Lower $headerPath);RETRIEVED_AT_UTC=(Get-Field $pr @('RETRIEVED_AT_UTC'));RETRIEVED_AT_LOCAL=(Get-Field $pr @('RETRIEVED_AT_LOCAL'));HTTP_STATUS=(Get-Field $pr @('HTTP_STATUS'));CONTENT_TYPE=(Get-Field $pr @('CONTENT_TYPE'));CONTENT_LENGTH=(Get-Field $pr @('CONTENT_LENGTH'));ETAG=(Get-Field $pr @('ETAG'));LAST_MODIFIED=(Get-Field $pr @('LAST_MODIFIED'));BYTES=(Get-FileBytes $target);SHA256=$actualSha;ZIP_VALID='TRUE';EXPECTED_MEMBER=$item.ExpectedMember;EXPECTED_MEMBER_PRESENT='TRUE';IMMUTABLE_STATUS='FROZEN_READ_ONLY';DOWNLOAD_STATUS='SKIPPED_VERIFIED_EXISTING';NOTES='Re-run: exact existing bytes matched prior manifest SHA and expected ZIP member.'})
                [void]$statusRows.Add([pscustomobject]@{STATE=$item.State;TABLE=$item.Table;FILE_NAME=$item.FileName;URL=$item.Url;STATUS='SKIPPED_VERIFIED_EXISTING';HTTP_STATUS=(Get-Field $pr @('HTTP_STATUS'));ATTEMPTS=0;BYTES=(Get-FileBytes $target);SHA256=$actualSha;MESSAGE='Existing immutable raw asset verified.'})
            }
        }
        if (-not $reuse) {
            $integrityFailure=$true
            [void]$statusRows.Add([pscustomobject]@{STATE=$item.State;TABLE=$item.Table;FILE_NAME=$item.FileName;URL=$item.Url;STATUS='FAILED_EXISTING_UNTRUSTED_OR_MISMATCH';HTTP_STATUS='';ATTEMPTS=0;BYTES=(Get-FileBytes $target);SHA256=(Get-Sha256Lower $target);MESSAGE='Target exists but cannot be proven identical to prior frozen manifest + expected ZIP member. It was not overwritten.'})
            Write-Log "Existing target cannot be safely reused; immutable file not overwritten: $target" 'ERROR'
        }
        if ($reuse) { continue } else { continue }
    }

    $tempBody="$target.part.$RunId"; $tempHeaders="$headerPath.part.$RunId"
    $res=Invoke-HttpWithRetry -Url $item.Url -TempBody $tempBody -TempHeaders $tempHeaders -MaxRetries $MaxRetries -RetryDelaySeconds $RetryDelaySeconds -TimeoutMinutes $TimeoutMinutes
    if (-not ($res.TransportSuccess -and $res.HttpSuccess)) {
        $downloadUnavailable=$true; Preserve-Failed -Body $tempBody -Headers $tempHeaders -Label $item.FileName
        [void]$statusRows.Add([pscustomobject]@{STATE=$item.State;TABLE=$item.Table;FILE_NAME=$item.FileName;URL=$item.Url;STATUS='FAILED_OFFICIAL_ASSET_UNAVAILABLE';HTTP_STATUS=$res.HttpStatus;ATTEMPTS=$res.Attempts;BYTES=0;SHA256='';MESSAGE=$(if ($res.ErrorMessage) {$res.ErrorMessage} else {"HTTP status $($res.HttpStatus)"})})
        Write-Log "Official asset unavailable for ${key}: HTTP=$($res.HttpStatus) error=$($res.ErrorMessage)" 'ERROR'; continue
    }
    $actualTempBytes=Get-FileBytes $tempBody
    $cl=(Get-SafeString $res.ContentLength).Trim()
    if ($cl -match '^[0-9]+$' -and [Int64]$cl -ne [Int64]$actualTempBytes) {
        $integrityFailure=$true; Preserve-Failed -Body $tempBody -Headers $tempHeaders -Label $item.FileName
        [void]$statusRows.Add([pscustomobject]@{STATE=$item.State;TABLE=$item.Table;FILE_NAME=$item.FileName;URL=$item.Url;STATUS='FAILED_CONTENT_LENGTH_MISMATCH';HTTP_STATUS=$res.HttpStatus;ATTEMPTS=$res.Attempts;BYTES=$actualTempBytes;SHA256='';MESSAGE=("Content-Length={0} actual_bytes={1}" -f $cl,$actualTempBytes)})
        Write-Log "Content-Length mismatch for ${key}: header=$cl actual=$actualTempBytes" 'ERROR'; continue
    }
    $zip=Test-ZipExpectedMember -Path $tempBody -ExpectedMember $item.ExpectedMember
    if (-not $zip.Valid) {
        $integrityFailure=$true; Preserve-Failed -Body $tempBody -Headers $tempHeaders -Label $item.FileName
        [void]$statusRows.Add([pscustomobject]@{STATE=$item.State;TABLE=$item.Table;FILE_NAME=$item.FileName;URL=$item.Url;STATUS='FAILED_ZIP_OR_MEMBER_VALIDATION';HTTP_STATUS=$res.HttpStatus;ATTEMPTS=$res.Attempts;BYTES=0;SHA256='';MESSAGE=$zip.Message})
        Write-Log "ZIP/member validation failed for ${key}: $($zip.Message)" 'ERROR'; continue
    }
    Move-Item -LiteralPath $tempBody -Destination $target
    Move-Item -LiteralPath $tempHeaders -Destination $headerPath
    try { (Get-Item -LiteralPath $target).IsReadOnly=$true } catch { Write-Log "Could not set read-only attribute on $target; bytes remain frozen by manifest/hash. $($_.Exception.Message)" 'WARN' }
    $sha=Get-Sha256Lower $target; $bytes=Get-FileBytes $target
    [void]$rawRows.Add([pscustomobject]@{STATE=$item.State;TABLE=$item.Table;OFFICIAL_URL=$item.Url;FINAL_URL=$res.FinalUrl;LOCAL_PATH=$target;HEADERS_LOCAL_PATH=$headerPath;HEADERS_SHA256=(Get-Sha256Lower $headerPath);RETRIEVED_AT_UTC=$res.RetrievedAtUtc;RETRIEVED_AT_LOCAL=$res.RetrievedAtLocal;HTTP_STATUS=$res.HttpStatus;CONTENT_TYPE=$res.ContentType;CONTENT_LENGTH=$res.ContentLength;ETAG=$res.ETag;LAST_MODIFIED=$res.LastModified;BYTES=$bytes;SHA256=$sha;ZIP_VALID='TRUE';EXPECTED_MEMBER=$item.ExpectedMember;EXPECTED_MEMBER_PRESENT='TRUE';IMMUTABLE_STATUS='FROZEN_READ_ONLY';DOWNLOAD_STATUS='DOWNLOADED_FROZEN';NOTES='Official FIA DataMart response body preserved byte-for-byte; headers separate; expected CSV member verified.'})
    [void]$statusRows.Add([pscustomobject]@{STATE=$item.State;TABLE=$item.Table;FILE_NAME=$item.FileName;URL=$item.Url;STATUS='DOWNLOADED_FROZEN';HTTP_STATUS=$res.HttpStatus;ATTEMPTS=$res.Attempts;BYTES=$bytes;SHA256=$sha;MESSAGE='HTTP success; ZIP readable; expected member present; immutable raw frozen.'})
    Write-Log "RAW frozen $key bytes=$bytes sha256=$sha"
}

Export-CsvAtomic -Rows @($rawRows) -Path $RawManifestPath
Export-CsvAtomic -Rows @($statusRows) -Path $DownloadStatusPath

$schemaRows=New-Object System.Collections.ArrayList
$linkRows=New-Object System.Collections.ArrayList
$designAuthorityFailure=$false; $schemaFailure=$false; $linkFailure=$false

if (-not $downloadUnavailable -and -not $integrityFailure -and $rawRows.Count -eq 9) {
    $designManifestPath=Join-Path $DesignRoot 'manifests\RAW_ASSET_MANIFEST_v01.csv'
    if (-not (Test-Path -LiteralPath $designManifestPath)) {
        $designAuthorityFailure=$true; Write-Log "Frozen raw-design manifest missing: $designManifestPath" 'ERROR'
    } else {
        $designManifestRows=@(Import-Csv -LiteralPath $designManifestPath)
        foreach ($st in @('CA','OR','WA')) {
            try {
                $evalid=$F0[$st]; $statePlan=@($Plan | Where-Object {$_.State -eq $st}); $stateCd=$statePlan[0].StateCd
                $plotZipName="${st}_PLOT.zip"; $ppsaZipName="${st}_POP_PLOT_STRATUM_ASSGN.zip"
                $plotZip=Join-Path (Join-Path $DesignRoot 'raw_table_zips') $plotZipName; $ppsaZip=Join-Path (Join-Path $DesignRoot 'raw_table_zips') $ppsaZipName
                $plotManifest=Find-DesignManifestRow -Rows $designManifestRows -FileName $plotZipName; $ppsaManifest=Find-DesignManifestRow -Rows $designManifestRows -FileName $ppsaZipName
                if ($null -eq $plotManifest -or $null -eq $ppsaManifest) { throw 'Frozen raw-design manifest does not contain PLOT and/or POP_PLOT_STRATUM_ASSGN asset row.' }
                foreach ($pair in @(@($plotZip,$plotManifest,"${st}_PLOT.csv"),@($ppsaZip,$ppsaManifest,"${st}_POP_PLOT_STRATUM_ASSGN.csv"))) {
                    $zp=$pair[0]; $mr=$pair[1]; $member=$pair[2]
                    if (-not (Test-Path -LiteralPath $zp)) { throw "Frozen raw-design ZIP missing: $zp" }
                    $expected=(Get-Field $mr @('SHA256','BODY_SHA256')).ToLowerInvariant(); $actual=Get-Sha256Lower $zp
                    if (-not $expected -or $expected -ne $actual) { throw "Frozen raw-design SHA mismatch: $zp expected=$expected actual=$actual" }
                    $zt=Test-ZipExpectedMember -Path $zp -ExpectedMember $member; if (-not $zt.Valid) { throw "Frozen raw-design ZIP/member invalid: $zp :: $($zt.Message)" }
                }
                $dStateDir=Join-Path $WorkingDir "frozen_design_$st"; if (-not (Test-Path $dStateDir)) {New-Item -ItemType Directory -Path $dStateDir -Force|Out-Null}
                $plotCsv=Join-Path $dStateDir "${st}_PLOT.csv"; $ppsaCsv=Join-Path $dStateDir "${st}_POP_PLOT_STRATUM_ASSGN.csv"
                Extract-ZipMemberReadOnlyCopy -ZipPath $plotZip -ExpectedMember "${st}_PLOT.csv" -Destination $plotCsv
                Extract-ZipMemberReadOnlyCopy -ZipPath $ppsaZip -ExpectedMember "${st}_POP_PLOT_STRATUM_ASSGN.csv" -Destination $ppsaCsv
                Write-Log "Building species-blind frozen F0 plot authority for $st EVALID=$evalid"
                $plotProf=Stream-PlotTable -Path $plotCsv; $ppsaProf=Stream-PpsaF0 -Path $ppsaCsv -TargetEvalid $evalid
                if ($ppsaProf.F0.Count -eq 0) { throw "No POP_PLOT_STRATUM_ASSGN membership found for frozen F0 EVALID $evalid" }
                $f0MissingPlot=0; $f0Inv2023=0
                foreach ($pcn in @($ppsaProf.F0.Keys)) { if (-not $plotProf.Plots.ContainsKey($pcn)) {$f0MissingPlot++} elseif ((Get-SafeString $plotProf.Plots[$pcn].INVYR) -eq '2023') {$f0Inv2023++} }
                [void]$linkRows.Add([pscustomobject]@{STATE=$st;F0_EVALID=$evalid;TABLE='FROZEN_F0_AUTHORITY';F0_PLOT_COUNT=$ppsaProf.F0.Count;F0_PLOT_ROWS_IN_PPSA=$ppsaProf.MembershipRows;FROZEN_PLOT_AUTHORITY_ROWS=$plotProf.RowCount;F0_PLOTS_MISSING_FROM_FROZEN_PLOT=$f0MissingPlot;F0_PLOTS_INVYR_2023=$f0Inv2023;OBS_ROWS='';OBS_ROWS_INVYR_2023='';OBS_F0_LINKED_ROWS='';OBS_F0_LINKED_UNIQUE_PLOTS='';OBS_F0_LINKED_2023_UNIQUE_PLOTS='';OBS_2023_ORPHAN_TO_FROZEN_PLOT='';LINKAGE_STATUS=$(if ($f0MissingPlot -eq 0 -and $f0Inv2023 -gt 0) {'PASS'} else {'FAIL'});NOTES='F0 identity derives only from frozen component EVALID + frozen official POP_PLOT_STRATUM_ASSGN -> frozen PLOT. Accepted F0/D09C package is not rebuilt.'})
                if ($f0MissingPlot -gt 0 -or $f0Inv2023 -eq 0) { $linkFailure=$true }

                foreach ($item in $statePlan) {
                    $raw=Join-Path $RawDir $item.FileName; $oStateDir=Join-Path $WorkingDir "obs_$st"; if (-not (Test-Path $oStateDir)){New-Item -ItemType Directory -Path $oStateDir -Force|Out-Null}
                    $csv=Join-Path $oStateDir $item.ExpectedMember
                    Extract-ZipMemberReadOnlyCopy -ZipPath $raw -ExpectedMember $item.ExpectedMember -Destination $csv
                    $header=Get-CsvHeader $csv; $col=Test-Columns -Header $header -Required $RequiredColumns[$item.Table]
                    [void]$schemaRows.Add([pscustomobject]@{STATE=$st;TABLE=$item.Table;EXPECTED_MEMBER=$item.ExpectedMember;HEADER_COLUMN_COUNT=$header.Count;REQUIRED_COLUMNS=([string]::Join(';',[string[]]$RequiredColumns[$item.Table]));MISSING_COLUMNS=$col.Missing;SCHEMA_STATUS=$(if ($col.Pass){'PASS'}else{'FAIL'});SPECIES_VALUE_FIELDS_READ='NO';NOTES='Header names only checked for species-related columns such as SPCD; species values were never accessed.'})
                    if (-not $col.Pass) { $schemaFailure=$true; continue }
                    Write-Log "Species-blind streaming linkage profile $st $($item.Table)"
                    $obs=Stream-ObsProfile -Path $csv -Table $item.Table -ExpectedStateCd $stateCd -FrozenPlots $plotProf.Plots -F0Plots $ppsaProf.F0
                    $ls='PASS'
                    $notes='Legal PLT_CN overlap with frozen F0 and 2023 temporal coverage demonstrated.'
                    if ($obs.Rows2023 -le 0 -or $obs.F0LinkedUnique -le 0 -or $obs.F0Linked2023Unique -le 0 -or $obs.WrongStateRows -gt 0 -or $obs.Orphan2023Unique -gt 0) { $ls='FAIL'; $linkFailure=$true; $notes='Temporal/linkage/state integrity requirement failed; see counts.' }
                    if ($item.Table -eq 'TREE') { $notes += ' Missing TREE rows for individual F0 plots are not treated as failure/non-detection is allowed; only positive legal linkage and current temporal coverage are required.' }
                    [void]$linkRows.Add([pscustomobject]@{STATE=$st;F0_EVALID=$evalid;TABLE=$item.Table;F0_PLOT_COUNT=$ppsaProf.F0.Count;F0_PLOT_ROWS_IN_PPSA=$ppsaProf.MembershipRows;FROZEN_PLOT_AUTHORITY_ROWS=$plotProf.RowCount;F0_PLOTS_MISSING_FROM_FROZEN_PLOT=$f0MissingPlot;F0_PLOTS_INVYR_2023=$f0Inv2023;OBS_ROWS=$obs.RowCount;OBS_ROWS_INVYR_2023=$obs.Rows2023;OBS_F0_LINKED_ROWS=$obs.F0Rows;OBS_F0_LINKED_UNIQUE_PLOTS=$obs.F0LinkedUnique;OBS_F0_LINKED_2023_UNIQUE_PLOTS=$obs.F0Linked2023Unique;OBS_2023_ORPHAN_TO_FROZEN_PLOT=$obs.Orphan2023Unique;LINKAGE_STATUS=$ls;NOTES=$notes})
                }
            } catch {
                $designAuthorityFailure=$true
                Write-Log "Frozen design/F0 authority verification failed for ${st}: $($_.Exception.Message)" 'ERROR'
                [void]$linkRows.Add([pscustomobject]@{STATE=$st;F0_EVALID=$F0[$st];TABLE='FROZEN_F0_AUTHORITY';F0_PLOT_COUNT='';F0_PLOT_ROWS_IN_PPSA='';FROZEN_PLOT_AUTHORITY_ROWS='';F0_PLOTS_MISSING_FROM_FROZEN_PLOT='';F0_PLOTS_INVYR_2023='';OBS_ROWS='';OBS_ROWS_INVYR_2023='';OBS_F0_LINKED_ROWS='';OBS_F0_LINKED_UNIQUE_PLOTS='';OBS_F0_LINKED_2023_UNIQUE_PLOTS='';OBS_2023_ORPHAN_TO_FROZEN_PLOT='';LINKAGE_STATUS='FAIL';NOTES=$_.Exception.Message})
            }
        }
    }
}

# Ensure required compact evidence files remain structurally useful even on a blocked run.
foreach ($item in $Plan) {
    if (@($schemaRows | Where-Object { $_.STATE -eq $item.State -and $_.TABLE -eq $item.Table }).Count -eq 0) {
        [void]$schemaRows.Add([pscustomobject]@{STATE=$item.State;TABLE=$item.Table;EXPECTED_MEMBER=$item.ExpectedMember;HEADER_COLUMN_COUNT='';REQUIRED_COLUMNS=([string]::Join(';',[string[]]$RequiredColumns[$item.Table]));MISSING_COLUMNS='';SCHEMA_STATUS='NOT_RUN_INPUT_BLOCKED';SPECIES_VALUE_FIELDS_READ='NO';NOTES='Structural parsing not run because an upstream required input/acquisition/integrity check blocked this run.'})
    }
    if (@($linkRows | Where-Object { $_.STATE -eq $item.State -and $_.TABLE -eq $item.Table }).Count -eq 0) {
        [void]$linkRows.Add([pscustomobject]@{STATE=$item.State;F0_EVALID=$F0[$item.State];TABLE=$item.Table;F0_PLOT_COUNT='';F0_PLOT_ROWS_IN_PPSA='';FROZEN_PLOT_AUTHORITY_ROWS='';F0_PLOTS_MISSING_FROM_FROZEN_PLOT='';F0_PLOTS_INVYR_2023='';OBS_ROWS='';OBS_ROWS_INVYR_2023='';OBS_F0_LINKED_ROWS='';OBS_F0_LINKED_UNIQUE_PLOTS='';OBS_F0_LINKED_2023_UNIQUE_PLOTS='';OBS_2023_ORPHAN_TO_FROZEN_PLOT='';LINKAGE_STATUS='NOT_RUN_INPUT_BLOCKED';NOTES='Species-blind linkage verification not run because an upstream required input/acquisition/integrity check blocked this run.'})
    }
}
foreach ($st in @('CA','OR','WA')) {
    if (@($linkRows | Where-Object { $_.STATE -eq $st -and $_.TABLE -eq 'FROZEN_F0_AUTHORITY' }).Count -eq 0) {
        [void]$linkRows.Add([pscustomobject]@{STATE=$st;F0_EVALID=$F0[$st];TABLE='FROZEN_F0_AUTHORITY';F0_PLOT_COUNT='';F0_PLOT_ROWS_IN_PPSA='';FROZEN_PLOT_AUTHORITY_ROWS='';F0_PLOTS_MISSING_FROM_FROZEN_PLOT='';F0_PLOTS_INVYR_2023='';OBS_ROWS='';OBS_ROWS_INVYR_2023='';OBS_F0_LINKED_ROWS='';OBS_F0_LINKED_UNIQUE_PLOTS='';OBS_F0_LINKED_2023_UNIQUE_PLOTS='';OBS_2023_ORPHAN_TO_FROZEN_PLOT='';LINKAGE_STATUS='NOT_RUN_INPUT_BLOCKED';NOTES='Frozen F0 authority linkage not run because an upstream required input/acquisition/integrity check blocked this run.'})
    }
}
Export-CsvAtomic -Rows @($schemaRows) -Path $SchemaPath
Export-CsvAtomic -Rows @($linkRows) -Path $LinkagePath

# Final status precedence: unavailable official asset first; then integrity/schema/linkage.
if ($downloadUnavailable) { $FinalStatus='INPUT_BLOCKED_OFFICIAL_ASSET_UNAVAILABLE' }
elseif ($integrityFailure -or $designAuthorityFailure -or $schemaFailure -or $linkFailure -or $rawRows.Count -ne 9) { $FinalStatus='INPUT_BLOCKED_INTEGRITY_OR_SCHEMA_FAILURE' }
else { $FinalStatus='GAP_CLOSED_READY_FOR_MAINLINE_D08C2_CONTRACT_FREEZE' }

$schemaPassCount=@($schemaRows | Where-Object {$_.SCHEMA_STATUS -eq 'PASS'}).Count
$linkPassCount=@($linkRows | Where-Object {$_.LINKAGE_STATUS -eq 'PASS'}).Count
$qcRows=@(
    [pscustomobject]@{CHECK_ID='AUTHORIZED_DOWNLOAD_PLAN_EXACT_9';STATUS=$(if($Plan.Count -eq 9){'PASS'}else{'FAIL'});DETAILS='Exactly CA/OR/WA x TREE/COND/SUBPLOT.'},
    [pscustomobject]@{CHECK_ID='NO_PLOT_REDOWNLOAD';STATUS='PASS';DETAILS='PLOT appears only as previously frozen local authority; no PLOT URL exists in acquisition plan.'},
    [pscustomobject]@{CHECK_ID='NO_NATIONAL_SQLITE_OR_OTHER_SOURCE';STATUS='PASS';DETAILS='No national SQLite, Little, GBIF, or other FIA state tables requested.'},
    [pscustomobject]@{CHECK_ID='RAW_ASSETS_9_FROZEN';STATUS=$(if($rawRows.Count -eq 9 -and -not $downloadUnavailable -and -not $integrityFailure){'PASS'}else{'FAIL'});DETAILS="verified_frozen=$($rawRows.Count)/9"},
    [pscustomobject]@{CHECK_ID='FROZEN_PLOT_PPSA_AUTHORITY_HASH_VERIFIED';STATUS=$(if(-not $designAuthorityFailure){'PASS'}else{'FAIL'});DETAILS='CA/OR/WA prior raw-design PLOT and POP_PLOT_STRATUM_ASSGN read only after prior manifest SHA verification.'},
    [pscustomobject]@{CHECK_ID='OBS_SCHEMA_REQUIRED_KEYS';STATUS=$(if($schemaPassCount -eq 9){'PASS'}else{'FAIL'});DETAILS=("schema_pass={0}/9; values of species identity fields not read." -f $schemaPassCount)},
    [pscustomobject]@{CHECK_ID='OBS_2023_TEMPORAL_AND_F0_PLT_CN_LINKAGE';STATUS=$(if($linkPassCount -eq 12){'PASS'}else{'FAIL'});DETAILS=("linkage_pass={0}/12 (3 frozen F0 authority rows + 9 observational table rows); does not require TREE on every F0 plot." -f $linkPassCount)},
    [pscustomobject]@{CHECK_ID='SPECIES_BLIND_SCOPE';STATUS='PASS';DETAILS='No species filtering, eligibility/survivor counts, grids, abundance/support/occupancy/detection, or D08C2 execution.'},
    [pscustomobject]@{CHECK_ID='SCIENTIFIC_OUTPUT_CHANGED';STATUS='PASS';DETAILS='NO. Acquisition/authority closure only.'},
    [pscustomobject]@{CHECK_ID='FINAL_TASK_STATUS';STATUS=$FinalStatus;DETAILS='Only authorized terminal status emitted.'}
)
Export-CsvAtomic -Rows $qcRows -Path $QcPath

# Registry delta — branch evidence only; does not edit the central Registry.
$registry=New-Object System.Collections.ArrayList
[void]$registry.Add([pscustomobject]@{TASK_ID=$TaskId;ENTRY_TYPE='TASK';AUTHORITY_IDENTITY=$TaskId;COMMIT_OR_VERSION='v01';LOCAL_PATH=$ObsRoot;SHA256='';BYTES='';TASK_STATUS=$FinalStatus;SCIENTIFIC_OUTPUT_CHANGED='NO';PUBLICATION_CANDIDATE='YES_COMPACT_EVIDENCE';ROLE='QC';NOTES='Data Search Line observational acquisition/authority closure; central Registry not modified.'})
[void]$registry.Add([pscustomobject]@{TASK_ID=$TaskId;ENTRY_TYPE='INPUT_AUTHORITY';AUTHORITY_IDENTITY='Q1-D08C2-PREFLIGHT-OBS-AUTHORITY-v01-20260904';COMMIT_OR_VERSION='0cfbc033e9fc49fdba4d8823df113b7862e172ea';LOCAL_PATH='';SHA256='';BYTES='';TASK_STATUS=$FinalStatus;SCIENTIFIC_OUTPUT_CHANGED='NO';PUBLICATION_CANDIDATE='YES';ROLE='Methods/QC';NOTES='Accepted preflight authority; not recomputed.'})
[void]$registry.Add([pscustomobject]@{TASK_ID=$TaskId;ENTRY_TYPE='INPUT_AUTHORITY';AUTHORITY_IDENTITY='Q1-FIA-T2-2023-RAW-DESIGN-FREEZE-v01-20260903';COMMIT_OR_VERSION='4bdec2bfc27a0b2de9a64abfc491e6dfea9f07eb';LOCAL_PATH=$DesignRoot;SHA256='';BYTES='';TASK_STATUS=$FinalStatus;SCIENTIFIC_OUTPUT_CHANGED='NO';PUBLICATION_CANDIDATE='YES';ROLE='Data/QC';NOTES='Frozen CA/OR/WA PLOT + design authority; no re-download.'})
[void]$registry.Add([pscustomobject]@{TASK_ID=$TaskId;ENTRY_TYPE='INPUT_AUTHORITY';AUTHORITY_IDENTITY='Q1_D09C_T2_FINAL_CORRECTION_v02';COMMIT_OR_VERSION='0ec3fce71258e38958ecbb7534f3635e2eb05a63';LOCAL_PATH='';SHA256='07cb461121c71ef46990fea3e0cf9d8f139fd873234b9f57910ff10c7c33752f';BYTES='';TASK_STATUS=$FinalStatus;SCIENTIFIC_OUTPUT_CHANGED='NO';PUBLICATION_CANDIDATE='YES';ROLE='Methods/QC';NOTES='Accepted F0/D09C final identity; F0 not rebuilt.'})
[void]$registry.Add([pscustomobject]@{TASK_ID=$TaskId;ENTRY_TYPE='CODE';AUTHORITY_IDENTITY='Q1_D08C2_CAORWA_OBS_GAP_CLOSURE_v01.ps1';COMMIT_OR_VERSION='v01';LOCAL_PATH=$PSCommandPath;SHA256=(Get-Sha256Lower $PSCommandPath);BYTES=(Get-FileBytes $PSCommandPath);TASK_STATUS=$FinalStatus;SCIENTIFIC_OUTPUT_CHANGED='NO';PUBLICATION_CANDIDATE='YES';ROLE='Code';NOTES='Local acquisition/species-blind structural verification code; no scientific analysis.'})
foreach ($r in @($rawRows)) {
    [void]$registry.Add([pscustomobject]@{TASK_ID=$TaskId;ENTRY_TYPE='NEW_RAW_ASSET';AUTHORITY_IDENTITY=("FIA_DATAMART_{0}_{1}" -f $r.STATE,$r.TABLE);COMMIT_OR_VERSION=(Get-SafeString $r.RETRIEVED_AT_UTC);LOCAL_PATH=$r.LOCAL_PATH;SHA256=$r.SHA256;BYTES=$r.BYTES;TASK_STATUS=$FinalStatus;SCIENTIFIC_OUTPUT_CHANGED='NO';PUBLICATION_CANDIDATE='NO_LOCAL_CANONICAL_RAW';ROLE='Data';NOTES=("Exact official URL: {0}; immutable original ZIP; 99_tmp/working copies are not canonical." -f $r.OFFICIAL_URL)})
}
Export-CsvAtomic -Rows @($registry) -Path $RegistryDeltaPath

# Result note.
$stateSummary=@()
foreach ($st in @('CA','OR','WA')) {
    $lr=@($linkRows | Where-Object {$_.STATE -eq $st -and $_.TABLE -in @('TREE','COND','SUBPLOT')})
    $ok=(@($lr | Where-Object {$_.LINKAGE_STATUS -eq 'PASS'}).Count -eq 3)
    $stateSummary += "- $st F0 EVALID $($F0[$st]): observational TREE/COND/SUBPLOT structural linkage = $(if($ok){'PASS'}else{'BLOCK/INCOMPLETE'})."
}
$note=@(
    "# Q1 corrected D08C2 — CA/OR/WA observational-data gap closure v01",
    "",
    "TASK_ID: $TaskId",
    "",
    "Final status: **$FinalStatus**",
    "",
    "## Scope",
    "Only the nine authorized official FIA DataMart state-table ZIPs were acquired/frozen: CA/OR/WA × TREE/COND/SUBPLOT. Previously frozen PLOT/design authority was read-only and SHA-verified. No PLOT was re-downloaded; no national SQLite or other source was accessed by the script.",
    "",
    "## Frozen F0 components",
    "- CA = 62301",
    "- OR = 412301",
    "- WA = 532301",
    "",
    "## State linkage summary"
) + $stateSummary + @(
    "",
    "## Interpretation boundary",
    "This closure is species-blind. TREE values used only PLT_CN/STATECD/INVYR for mechanical linkage and temporal coverage; SPCD was checked only as a column name. No species identity values, eligibility, survivor counts, abundance/support, occupancy/detection, grid construction, or corrected D08C2 analysis were produced.",
    "",
    "Absence of a TREE row for an individual F0 PLOT is not treated as linkage failure because a plot may legitimately have no TREE record; the check requires positive legal linkage at table/state level and 2023 temporal coverage.",
    "",
    "## Authorities",
    "- Preflight: Q1-D08C2-PREFLIGHT-OBS-AUTHORITY-v01-20260904 @ 0cfbc033e9fc49fdba4d8823df113b7862e172ea",
    "- CA/OR/WA raw-design freeze: Q1-FIA-T2-2023-RAW-DESIGN-FREEZE-v01-20260903 @ 4bdec2bfc27a0b2de9a64abfc491e6dfea9f07eb",
    "- Accepted F0 / D09C final: Q1_D09C_T2_FINAL_CORRECTION_v02 @ 0ec3fce71258e38958ecbb7534f3635e2eb05a63; reproducible ZIP SHA-256 07cb461121c71ef46990fea3e0cf9d8f139fd873234b9f57910ff10c7c33752f",
    "",
    "## STOP",
    "No corrected D08C2 was run. Mainline must freeze the next contract before any species-level or Q1 computation."
)
$note | Set-Content -LiteralPath $ResultNotePath -Encoding UTF8

Write-Log "END $TaskId final_status=$FinalStatus raw_assets=$($rawRows.Count)/9 schema_rows=$($schemaRows.Count) linkage_rows=$($linkRows.Count)"

# SHA256SUMS: raw assets, response headers and compact outputs. Working copies are deliberately excluded.
$sumRows=New-Object System.Collections.ArrayList
$hashFiles=@()
$hashFiles += @(Get-ChildItem -LiteralPath $RawDir -File -Filter '*.zip' | Where-Object {$_.Name -in $allowedFiles})
$hashFiles += @(Get-ChildItem -LiteralPath $HeaderDir -File -Filter '*.headers.txt')
$hashFiles += @(Get-ChildItem -LiteralPath $FailedDir -File -ErrorAction SilentlyContinue)
$hashFiles += @($RawManifestPath,$DownloadStatusPath,$LinkagePath,$SchemaPath,$QcPath,$ResultNotePath,$RegistryDeltaPath,$LogPath,$PSCommandPath) | Where-Object {Test-Path -LiteralPath $_} | ForEach-Object {Get-Item -LiteralPath $_}
foreach ($f in @($hashFiles | Sort-Object FullName -Unique)) {
    $role=if ($f.FullName -eq $PSCommandPath) {'CODE'} elseif ($f.FullName -like "$RawDir*") {'OFFICIAL_RAW_TABLE_ZIP'} elseif ($f.FullName -like "$HeaderDir*") {'HTTP_HEADERS'} elseif ($f.Name -eq 'REGISTRY_DELTA_v01.csv') {'REGISTRY_DELTA'} elseif ($f.FullName -like "$QcDir*") {'QC'} elseif ($f.FullName -like "$OutputDir*") {'COMPACT_EVIDENCE'} elseif ($f.FullName -like "$LogDir*") {'LOG'} else {'MANIFEST'}
    [void]$sumRows.Add([pscustomobject]@{FILE=$f.FullName;BYTES=$f.Length;SHA256=(Get-Sha256Lower $f.FullName);ROLE=$role})
}
Export-CsvAtomic -Rows @($sumRows) -Path $ShaPath

# Relay v0.2.2 native payload — compact evidence only; raw ZIPs remain local canonical authority.
$payloadFiles=@(
    [pscustomobject]@{Source=$ResultNotePath;Rel='outputs/Q1_D08C2_CAORWA_OBS_RESULT_NOTE_v01.md';Role='result_note';Target='mirror';Required='yes';Priority='high';Notes='Read first: terminal status and scope boundary.'},
    [pscustomobject]@{Source=$LinkagePath;Rel='outputs/Q1_D08C2_CAORWA_OBS_F0_LINKAGE_CHECK_v01.csv';Role='evidence';Target='mirror';Required='yes';Priority='high';Notes='Species-blind PLT_CN/F0/2023 structural linkage evidence.'},
    [pscustomobject]@{Source=$SchemaPath;Rel='outputs/Q1_D08C2_CAORWA_OBS_SCHEMA_CHECK_v01.csv';Role='evidence';Target='mirror';Required='yes';Priority='high';Notes='Required observational table fields; no species values read.'},
    [pscustomobject]@{Source=$RawManifestPath;Rel='manifests/Q1_D08C2_CAORWA_OBS_RAW_ASSET_MANIFEST_v01.csv';Role='raw_asset_manifest';Target='mirror';Required='yes';Priority='high';Notes='Exact official URL/local path/bytes/SHA/HTTP/ZIP/member evidence for all nine raw assets.'},
    [pscustomobject]@{Source=$DownloadStatusPath;Rel='manifests/Q1_D08C2_CAORWA_OBS_DOWNLOAD_STATUS_v01.csv';Role='download_status';Target='mirror';Required='yes';Priority='high';Notes='Per-asset download status.'},
    [pscustomobject]@{Source=$QcPath;Rel='qc/Q1_D08C2_CAORWA_OBS_GAP_CLOSURE_QC_v01.csv';Role='qc';Target='mirror';Required='yes';Priority='high';Notes='Gap-closure QC and final status.'},
    [pscustomobject]@{Source=$RegistryDeltaPath;Rel='manifests/REGISTRY_DELTA_v01.csv';Role='registry_delta';Target='mirror';Required='yes';Priority='high';Notes='Branch-only registry delta; central Registry not modified.'},
    [pscustomobject]@{Source=$ShaPath;Rel='manifests/SHA256SUMS.csv';Role='integrity_manifest';Target='mirror';Required='yes';Priority='high';Notes='Raw/header/compact evidence SHA-256 ledger.'},
    [pscustomobject]@{Source=$LogPath;Rel=("logs/{0}" -f [System.IO.Path]::GetFileName($LogPath));Role='log';Target='mirror';Required='yes';Priority='normal';Notes='Acquisition/verification execution log.'},
    [pscustomobject]@{Source=$PSCommandPath;Rel='code/Q1_D08C2_CAORWA_OBS_GAP_CLOSURE_v01.ps1';Role='code';Target='mirror';Required='yes';Priority='high';Notes='Exact local acquisition/verification code used.'}
)
foreach ($ff in @(Get-ChildItem -LiteralPath $FailedDir -File -ErrorAction SilentlyContinue | Sort-Object Name)) {
    $payloadFiles += [pscustomobject]@{Source=$ff.FullName;Rel=("failed_responses/{0}" -f $ff.Name);Role='failed_http_evidence';Target='mirror';Required='yes';Priority='high';Notes='Preserved failed response/header evidence from acquisition attempts; included only for audit.'}
}
$transferRows=New-Object System.Collections.ArrayList
foreach ($pf in $payloadFiles) {
    if (-not (Test-Path -LiteralPath $pf.Source)) { continue }
    $dest=Join-Path $RelayRoot ($pf.Rel -replace '/','\'); $parent=Split-Path -Parent $dest; if (-not (Test-Path $parent)){New-Item -ItemType Directory -Path $parent -Force|Out-Null}
    Copy-Item -LiteralPath $pf.Source -Destination $dest -Force
    $fi=Get-Item -LiteralPath $dest
    [void]$transferRows.Add([pscustomobject]@{local_path=$fi.FullName;relative_path=$pf.Rel;role=$pf.Role;upload_target=$pf.Target;required=$pf.Required;mainline_priority=$pf.Priority;size_bytes=$fi.Length;sha256=(Get-Sha256Lower $fi.FullName);notes=$pf.Notes})
}
Export-CsvAtomic -Rows @($transferRows) -Path $TransferManifestPath

Write-Host ''
Write-Host '===== Q1 corrected D08C2 CA/OR/WA OBSERVATIONAL GAP CLOSURE v01 ====='
Write-Host ("FINAL_STATUS = {0}" -f $FinalStatus)
Write-Host ("RAW_ASSET_MANIFEST = {0}" -f $RawManifestPath)
Write-Host ("DOWNLOAD_STATUS = {0}" -f $DownloadStatusPath)
Write-Host ("F0_LINKAGE_CHECK = {0}" -f $LinkagePath)
Write-Host ("SCHEMA_CHECK = {0}" -f $SchemaPath)
Write-Host ("QC = {0}" -f $QcPath)
Write-Host ("RESULT_NOTE = {0}" -f $ResultNotePath)
Write-Host ("SHA256SUMS = {0}" -f $ShaPath)
Write-Host ("REGISTRY_DELTA = {0}" -f $RegistryDeltaPath)
Write-Host ("TRANSFER_MANIFEST = {0}" -f $TransferManifestPath)
Write-Host ("LOG = {0}" -f $LogPath)
Write-Host 'STOP: corrected D08C2 was NOT run.'
if ($FinalStatus -eq 'GAP_CLOSED_READY_FOR_MAINLINE_D08C2_CONTRACT_FREEZE') { exit 0 }
elseif ($FinalStatus -eq 'INPUT_BLOCKED_OFFICIAL_ASSET_UNAVAILABLE') { exit 3 }
else { exit 4 }
