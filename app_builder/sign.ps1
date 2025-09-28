param(
    # The full path to the file you want to sign (e.g., an executable or script).
    [Parameter(Mandatory=$true)]
    [string]$FilePath,

    # The file path to the certificate (e.g., a .pfx file) OR the certificate's thumbprint 
    # if it's stored in the Certificate Store.
    [Parameter(Mandatory=$true)]
    [string]$CertSource,
    
    # Password for the certificate file (if a .pfx is used).
    [string]$CertPassword = "",

    # Optional: Specifies the SignTool.exe path. If not provided, the script will search for it.
    [string]$SignToolPath = ""
)

# ---
## Function to find SignTool.exe dynamically

function Find-SignTool {
    param([string]$DefaultPath)

    if (-not [string]::IsNullOrWhiteSpace($DefaultPath) -and (Test-Path $DefaultPath)) {
        return $DefaultPath
    }

    Write-Host "Searching for SignTool.exe..." -ForegroundColor Yellow

    # Common search path for Windows Kits 10/11
    $SearchPath = Join-Path -Path ${env:ProgramFiles(x86)} -ChildPath "Windows Kits\10\bin"
    
    # Use Get-ChildItem to find the newest version of signtool.exe recursively
    $SignTool = Get-ChildItem -Path $SearchPath -Filter "signtool.exe" -Recurse -ErrorAction SilentlyContinue |
                Sort-Object -Property LastWriteTime -Descending |
                Select-Object -First 1 -ExpandProperty FullName

    if ($SignTool) {
        return $SignTool
    } else {
        Write-Error "SignTool.exe not found in Windows Kits directory. Please specify it using the -SignToolPath parameter."
        return $null
    }
}

# ---
## Main Logic

# 1. Locate SignTool
$signTool = Find-SignTool -DefaultPath $SignToolPath
if (-not $signTool) {
    exit 1
}

# 2. Validate File to Sign
if (-not (Test-Path $FilePath -PathType Leaf)) {
    Write-Error "File to sign not found: '$FilePath'."
    exit 1
}

# 3. Determine SignTool Arguments based on CertSource
$SignToolArgs = @("sign")

if (Test-Path $CertSource -PathType Leaf) {
    # CertSource is treated as a file (e.g., .pfx)
    Write-Host "Using certificate file: $CertSource" -ForegroundColor Cyan
    $SignToolArgs += "/f", $CertSource
    
    # Add password if provided
    if (-not [string]::IsNullOrWhiteSpace($CertPassword)) {
        $SignToolArgs += "/p", $CertPassword
    } else {
        Write-Warning "No password provided for the certificate file. Signing may fail if the file is protected."
    }

} elseif ((Get-ChildItem "Cert:\CurrentUser\My" | Where-Object {$_.Thumbprint -eq $CertSource}) -or (Get-ChildItem "Cert:\LocalMachine\My" | Where-Object {$_.Thumbprint -eq $CertSource})) {
    # CertSource is treated as a thumbprint
    Write-Host "Using certificate with thumbprint: $CertSource from Certificate Store." -ForegroundColor Cyan
    $SignToolArgs += "/sha1", $CertSource

} else {
    Write-Error "Certificate source ('$CertSource') is neither a valid file path nor a valid certificate thumbprint."
    exit 1
}

# 4. Standard Signing Parameters
$SignToolArgs += "/tr", "http://timestamp.digicert.com" # Trusted Time Stamping URL
$SignToolArgs += "/td", "SHA256" # Timestamp Digest Algorithm
$SignToolArgs += "/fd", "SHA256" # File Digest Algorithm
$SignToolArgs += "/a" # Automatically select the best signing cert (if using SHA1/thumbprint)
$SignToolArgs += $FilePath

# 5. Execute SignTool
Write-Host "Signing '$FilePath'..." -ForegroundColor Green
Write-Host "Executing: $signTool $($SignToolArgs -join ' ')" -ForegroundColor DarkGray

try {
    & $signTool $SignToolArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Signing successful!" -ForegroundColor Green
    } else {
        Write-Error "❌ Signing failed. SignTool Exit Code: $LASTEXITCODE. Check the output above for details."
        exit 1
    }
}
catch {
    Write-Error "An unhandled error occurred while executing SignTool. Error: $($_.Exception.Message)"
    exit 1
}

# Usage: .\Sign-FileWithCert.ps1 -FilePath <String> -CertSource <String> [-CertPassword <String>] [-SignToolPath <String>]
# Parameter     Required	Type	Description
#FilePath       Yes	        String	The full path to the file you want to digitally sign (e.g., C:\MyApp\App.exe).
#CertSource     Yes	        String	Either the full path to a certificate file (like a .pfx) OR the Thumbprint of a certificate in your Windows Certificate Store.
#CertPassword	No	        String	The password for the certificate file specified in -CertSource (only required if using a protected .pfx file).
#SignToolPath	No	        String	The explicit path to signtool.exe. If omitted, the script automatically searches for the newest version in the Windows Kits directory.