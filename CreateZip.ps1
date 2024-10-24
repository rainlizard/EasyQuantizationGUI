# Define the zip file name and subdirectory name
$zipName = "EasyQuantizationGUI.zip"
$subDirName = "EasyQuantizationGUI"

# Get the current directory
$sourcePath = (Get-Location).Path
Write-Host "Current directory: $sourcePath"

# Create temp directory in Windows temp folder
$tempDir = Join-Path $env:TEMP "EasyQuantizationGUI_temp"
$tempSubDir = Join-Path $tempDir $subDirName

if (Test-Path $tempDir) {
   Remove-Item -Recurse -Force $tempDir
}
New-Item -Path $tempSubDir -ItemType Directory -Force | Out-Null
Write-Host "Created temp directory: $tempSubDir"

# Copy files (excluding .git, .zip, .ps1, and README.md)
$filesCopied = 0
Get-ChildItem -File | Where-Object {
   $_.Name -ne $zipName -and 
   $_.Name -ne "README.md" -and
   $_.Extension -ne ".zip" -and 
   $_.Extension -ne ".ps1" -and 
   $_.FullName -notlike "*.git*"
} | ForEach-Object {
   Copy-Item $_.FullName -Destination $tempSubDir
   Write-Host "Copied file: $($_.Name)"
   $filesCopied++
}

Write-Host "Copied $filesCopied files to temp directory"

# Create zip
$zipPath = Join-Path $sourcePath $zipName
Write-Host "Creating zip file at: $zipPath"
Add-Type -Assembly "System.IO.Compression.FileSystem"
[System.IO.Compression.ZipFile]::CreateFromDirectory($tempDir, $zipPath)

# Verify zip was created
if (Test-Path $zipPath) {
   Write-Host "Successfully created zip file: $zipPath"
} else {
   Write-Host "ERROR: Zip file was not created!"
}

# Cleanup
Remove-Item -Recurse -Force $tempDir
Write-Host "Cleaned up temp directory"