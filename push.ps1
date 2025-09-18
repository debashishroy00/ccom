param (
    [string]$Message = ""
)

# Default commit message with timestamp if none provided
if (-not $Message -or $Message -eq "") {
    $date = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $Message = "auto-commit $date"
}

Write-Host "=== Commit message: $Message" -ForegroundColor Cyan

# Ensure we're in a git repo
git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not inside a git repository." -ForegroundColor Red
    exit 1
}

# Detect branch (prefer main, else master)
$branch = git branch --show-current
if ($branch -ne "main" -and $branch -ne "master") {
    if (git rev-parse --verify main 2>$null) {
        git switch main
        $branch = "main"
    } elseif (git rev-parse --verify master 2>$null) {
        git switch master
        $branch = "master"
    } else {
        Write-Host "No main or master branch found." -ForegroundColor Red
        exit 1
    }
}

Write-Host "=== On branch $branch" -ForegroundColor Yellow

# Stage everything
git add -A

# Only commit if there are staged changes
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "$Message"
} else {
    Write-Host "Nothing new to commit." -ForegroundColor DarkYellow
}

# Push to origin
git push -u origin $branch
