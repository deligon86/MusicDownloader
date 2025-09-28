param(
    # The full path where the certificate file (.cer) will be saved. 
    # The directory will be created if it doesn't exist.
    [Parameter(Mandatory=$true)]
    [string]$FilePath,

    # The common name (CN) for the subject of the certificate. 
    # Used for the certificate name and the exported filename.
    [Parameter(Mandatory=$true)]
    [string]$CertName,

    # The number of days the certificate should be valid. Defaults to 365 days (1 year).
    [int]$NotAfterDays = 365
)

# ---
## Robust File Path and Directory Handling

try {
    # Check if the directory exists, and create it if it doesn't
    if (-not (Test-Path -Path $FilePath -PathType Container)) {
        Write-Host "Creating directory: '$FilePath'" -ForegroundColor Yellow
        New-Item -Path $FilePath -ItemType Directory | Out-Null
    }
}
catch {
    Write-Error "Failed to create directory '$FilePath'. Error: $($_.Exception.Message)"
    exit 1
}

$FullCertPath = Join-Path -Path $FilePath -ChildPath "$CertName.cer"

# ---
## Certificate Generation

try {
    Write-Host "Generating self-signed certificate for '$CertName'..." -ForegroundColor Cyan

    # Calculate the NotAfter date based on the current date and $NotAfterDays
    $NotAfterDate = (Get-Date).AddDays($NotAfterDays)

    $cert = New-SelfSignedCertificate `
        -Subject "CN=$CertName" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -KeyExportPolicy Exportable `
        -KeySpec Signature `
        -KeyLength 2048 `
        -KeyAlgorithm RSA `
        -HashAlgorithm SHA256 `
        -NotAfter $NotAfterDate # Set the validity period
    
    Write-Host "Certificate generated successfully." -ForegroundColor Green
    Write-Host "Thumbprint: $($cert.Thumbprint)"
    Write-Host "Valid Until: $($cert.NotAfter)"

    # ---
    ## Certificate Export

    Write-Host "Exporting certificate to '$FullCertPath'..." -ForegroundColor Cyan
    
    Export-Certificate -Cert $cert -FilePath $FullCertPath

    Write-Host "Export successful! The certificate is saved to:" -ForegroundColor Green
    Write-Host "$FullCertPath" -ForegroundColor Green
}
catch {
    Write-Error "An error occurred during certificate generation or export. Error: $($_.Exception.Message)"
    exit 1
}

# Usage: .\New-SelfSignedExportableCert.ps1 -FilePath <String> -CertName <String> [-NotAfterDays <Int32>]
# Parameter     Required	Type	Description
# FilePath      Yes	        String	The destination directory where the .cer file will be saved. The directory is created if it doesn't exist.
# CertName      Yes	        String	The Common Name (CN) for the certificate's subject and the base name for the exported file (e.g., MyWebAppCert).
# NotAfterDays	No	        Int32	The number of days the certificate will be valid. Default is 365 (1 year).
