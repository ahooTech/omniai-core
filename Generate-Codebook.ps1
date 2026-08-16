<#
.\Generate-Codebook.ps1 -ProjectPath "C:\Users\DAYLIFF\Desktop\omniai-core"
#>


param(
    [string]$ProjectPath = (Get-Location).Path,
    [switch]$GeneratePdf
)

# ============================================================
# Configuration
# ============================================================

$Root = (Resolve-Path $ProjectPath).Path

$MarkdownFile = Join-Path $Root "Codebase.md"
$PdfFile      = Join-Path $Root "Codebase.pdf"

$ExcludedDirectories = @(
    ".git",
    ".github",
    "node_modules",
    "coverage",
    "dist",
    "build",
    "bin",
    "obj",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "migrations"
)

$ExcludedExtensions = @(
    ".png",".jpg",".jpeg",".gif",".bmp",".ico",".svg",".webp",".avif",
    ".pdf",".zip",".7z",".rar",
    ".exe",".dll",".so",
    ".woff",".woff2",".ttf",".eot",
    ".pyc",".class",".db",".sqlite3",".log"
)

# Delete old markdown if it exists
if (Test-Path $MarkdownFile) {
    Remove-Item $MarkdownFile -Force
}

# ============================================================
# Helper Function
# ============================================================

function Add-Line {
    param([string]$Text)

    Add-Content -Path $MarkdownFile -Value $Text -Encoding UTF8
}

# ============================================================
# Scan Files
# ============================================================

Write-Host ""
Write-Host "Scanning repository..."
Write-Host ""

$Files = Get-ChildItem -Path $Root -Recurse -File | Where-Object {

    $relative = $_.FullName.Substring($Root.Length).TrimStart('\')

    foreach ($dir in $ExcludedDirectories) {
        if ($relative -split "\\" -contains $dir) {
            return $false
        }
    }

    if ($ExcludedExtensions -contains $_.Extension.ToLower()) {
        return $false
    }

    return $true

} | Sort-Object FullName

Write-Host "Found $($Files.Count) files."
Write-Host ""

# ============================================================
# Markdown Header
# ============================================================

Add-Line "# Staff Canteen Management System"
Add-Line ""
Add-Line "Generated: $(Get-Date)"
Add-Line ""
Add-Line "---"
Add-Line ""

# ============================================================
# Table of Contents
# ============================================================

Add-Line "## Table of Contents"
Add-Line ""

foreach ($file in $Files) {

    $relative = $file.FullName.Substring($Root.Length).TrimStart('\')

    Add-Line "- $relative"

}

Add-Line ""
Add-Line "---"
Add-Line ""

# ============================================================
# Add Every File
# ============================================================

$index = 1

foreach ($file in $Files) {

    $relative = $file.FullName.Substring($Root.Length).TrimStart('\')

    Write-Host "[$index/$($Files.Count)] $relative"

    $language = $file.Extension.TrimStart('.')

    if ([string]::IsNullOrWhiteSpace($language)) {
        $language = "text"
    }

    Add-Line ""
    Add-Line "<div style='page-break-after: always;'></div>"
    Add-Line ""
    Add-Line "# File: $relative"
    Add-Line ""

    # Opening code fence
    Add-Line ('```' + $language)

    try {

        $content = Get-Content $file.FullName -Raw -Encoding UTF8

        Add-Content -Path $MarkdownFile -Value $content -Encoding UTF8

    }
    catch {

        Add-Line "[Unable to read file.]"

    }

    # Closing code fence
    Add-Line '```'
    Add-Line ""

    $index++

}

Write-Host ""
Write-Host "Markdown created successfully!"
Write-Host ""
Write-Host $MarkdownFile

# ============================================================
# Optional PDF Generation
# ============================================================

if ($GeneratePdf) {

    $Pandoc = Get-Command pandoc -ErrorAction SilentlyContinue

    if ($Pandoc) {

        Write-Host ""
        Write-Host "Generating PDF..."

        & pandoc `
            $MarkdownFile `
            -o $PdfFile `
            --toc `
            --highlight-style=tango

        Write-Host ""
        Write-Host "PDF created:"
        Write-Host $PdfFile

    }
    else {

        Write-Host ""
        Write-Host "Pandoc was not found."
        Write-Host ""
        Write-Host "Install it from:"
        Write-Host "https://pandoc.org/installing.html"

    }

}



# The attached is a project structure with all it's files. I wan't to generate its, codebase using this
# script " "  
# so I don't know the excluded directories and extensions I should add in the script. 
# The goal is for me to give you the code, understernd it and tell me the visible projects that are
# fixes we can apply to it for highest possible visibility.