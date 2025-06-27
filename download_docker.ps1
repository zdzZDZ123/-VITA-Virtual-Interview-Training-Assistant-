# Docker Desktop Download Script
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

$dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$outputPath = "D:\docker_install\Docker_Desktop_Installer.exe"

Write-Host "Downloading Docker Desktop..."
Write-Host "URL: $dockerUrl"
Write-Host "Saving to: $outputPath"

try {
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($dockerUrl, $outputPath)
    Write-Host "Download completed!"
    
    if (Test-Path $outputPath) {
        $fileSize = (Get-Item $outputPath).Length / 1MB
        Write-Host "File size: $([math]::Round($fileSize, 2)) MB"
        Write-Host "File path: $outputPath"
    }
} catch {
    Write-Host "Download failed: $($_.Exception.Message)"
    
    Write-Host "Trying alternative download method..."
    try {
        Invoke-WebRequest -Uri $dockerUrl -OutFile $outputPath -UseBasicParsing -TimeoutSec 300
        Write-Host "Alternative method succeeded!"
    } catch {
        Write-Host "Alternative method also failed: $($_.Exception.Message)"
        Write-Host "Please download Docker Desktop manually or check network connection"
    }
} 