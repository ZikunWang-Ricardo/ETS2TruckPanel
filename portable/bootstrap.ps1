param([switch]$Rollback,[switch]$Check)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$root=Split-Path -Parent $PSScriptRoot
$runtime=Join-Path $root '_setup_runtime'
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $checksums=Get-Content -LiteralPath (Join-Path $root 'checksums.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $algorithm=[Security.Cryptography.SHA256]::Create()
    $stream=[IO.File]::OpenRead((Join-Path $root 'TouchTruck.tpp'))
    try { $actual=[BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
    if($actual -ne $checksums.'TouchTruck.tpp') { throw 'Plugin/runtime package checksum mismatch.' }
    [IO.Directory]::CreateDirectory($runtime) | Out-Null
    $zip=[IO.Compression.ZipFile]::OpenRead((Join-Path $root 'TouchTruck.tpp'))
    try {
        foreach($entry in $zip.Entries) {
            if($entry.FullName.StartsWith('TouchTruck/runtime/')) {
                $name=$entry.FullName.Substring('TouchTruck/runtime/'.Length)
                if($name -match '^[A-Za-z0-9_.-]+$') {
                    [IO.Compression.ZipFileExtensions]::ExtractToFile($entry,(Join-Path $runtime $name),$true)
                }
            }
        }
    } finally { $zip.Dispose() }
    $python=Join-Path $runtime 'python.exe'
    if(!(Test-Path -LiteralPath $python)) { throw 'Embedded Python is missing.' }
    $arguments=@('-X','utf8',(Join-Path $PSScriptRoot 'install.py'))
    if($Rollback) { $arguments+='--rollback' }
    if($Check) { $arguments+='--check' }
    & $python @arguments
    exit $LASTEXITCODE
} catch {
    Write-Host $_ -ForegroundColor Red
    exit 1
}
