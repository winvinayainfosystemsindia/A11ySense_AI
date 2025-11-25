param (
    [string]$Path = ".",
    [string[]]$Extensions = @()  # Example: @("py", "js", "json")
)

Write-Host "Scanning directory: $Path" -ForegroundColor Cyan

# If extensions are provided, build a filter
$files = if ($Extensions.Count -gt 0) {
    Get-ChildItem -Path $Path -Recurse -File | Where-Object {
        $ext = $_.Extension.TrimStart('.').ToLower()
        $Extensions -contains $ext
    }
} else {
    Get-ChildItem -Path $Path -Recurse -File
}

foreach ($file in $files) {
    # Get relative path
    $relativePath = $file.FullName.Replace((Resolve-Path $Path), "").TrimStart("\/")
    Write-Output $relativePath
}
