# Root project folder
$root = "accessibility-audit-tool"
New-Item -ItemType Directory -Path $root -Force | Out-Null

# Directory structure array
$dirs = @(
    "config",
    "src",
    "src/core",
    "src/crawler",
    "src/crawler/anti_blocking",
    "src/analyzer",
    "src/llm",
    "src/reporting",
    "src/utils",
    "tests",
    "tests/test_crawler",
    "tests/test_analyzer",
    "tests/test_llm",
    "tests/test_reporting",
    "storage",
    "storage/logs",
    "storage/reports",
    "storage/temp",
    "scripts",
    "requirements",
    "docs"
)

# Create directories
foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Path "$root/$dir" -Force | Out-Null
}

# Files to create
$files = @(
    "config/config.yaml",
    "config/__init__.py",

    "src/__init__.py",
    "src/core/__init__.py",
    "src/core/exceptions.py",
    "src/core/constants.py",

    "src/crawler/__init__.py",
    "src/crawler/base_crawler.py",
    "src/crawler/playwright_crawler.py",
    "src/crawler/sitemap_parser.py",
    "src/crawler/url_filter.py",
    "src/crawler/anti_blocking/__init__.py",
    "src/crawler/anti_blocking/cloudflare_bypass.py",
    "src/crawler/anti_blocking/stealth_handler.py",

    "src/analyzer/__init__.py",
    "src/analyzer/axe_analyzer.py",

    "src/llm/__init__.py",
    "src/llm/groq_client.py",

    "src/reporting/__init__.py",
    "src/reporting/excel_reporter.py",
    "src/reporting/report_generator.py",

    "src/utils/__init__.py",
    "src/utils/logger.py",
    "src/utils/file_utils.py",
    "src/utils/validators.py",

    "tests/__init__.py",
    "tests/conftest.py",

    "scripts/run_audit.py",
    "scripts/setup.py",

    "requirements/base.txt",
    "requirements/dev.txt",
    "requirements/prod.txt",

    "docs/architecture.md",

    ".env.example",
    ".gitignore",
    "pyproject.toml",
    "README.md",
    "main.py"
)

# Create files
foreach ($file in $files) {
    New-Item -ItemType File -Path "$root/$file" -Force | Out-Null
}

Write-Host "✔ Project directory structure created successfully!"
