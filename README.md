```
accessibility-audit-tool/
├── .env.example
├── .gitignore
├── AccessibilityAuditTool.spec
├── build.py
├── create_structure.ps1
├── GetProjectFiles.ps1
├── main.py
├── pyproject.toml
├── README.md
├── requirements.txt
├── setup_tool.py
│
├── AccessibilityAuditTool_Package/
│   ├── AccessibilityAuditTool.exe
│   ├── Setup.bat
│   ├── setup_tool.py
│   └── config/
│       ├── config.yaml
│       ├── license_config.json
│       └── __init__.py
│
├── config/
│   ├── config.yaml
│   ├── license_config.json
│   └── __init__.py
│
├── dist/
│   └── AccessibilityAuditTool.exe
│
├── docs/
│   ├── architecture.md
│   └── logo/
│       ├── Generated Image November 18, 2025 - 5_04PM (1).png
│       ├── Generated Image November 18, 2025 - 5_04PM.png
│       ├── Generated Image November 18, 2025 - 5_05PM.png
│       └── Generated Image November 18, 2025 - 5_06PM.png
│
├── others/
│   └── analyzers/
│       ├── cognitive_analyzer.py
│       ├── content_analyzer.py
│       ├── dynamic_interaction_analyzer.py
│       ├── interactive_analyzer.py
│       ├── navigation_analyzer.py
│       ├── performance_analyzer.py
│       └── __init__.py
│
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
│
├── scripts/
│   ├── run_audit.py
│   └── setup.py
│
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   └── __init__.py
│   │
│   ├── crawler/
│   │   ├── advanced_url_discovery.py
│   │   ├── base_crawler.py
│   │   ├── content_analyzer.py
│   │   ├── error_handler.py
│   │   ├── performance_monitor.py
│   │   ├── playwright_crawler.py
│   │   ├── sitemap_parser.py
│   │   ├── url_filter.py
│   │   ├── __init__.py
│   │   └── anti_blocking/
│   │       ├── cloudflare_bypass.py
│   │       ├── stealth_handler.py
│   │       └── __init__.py
│   │
│   ├── analyzer/
│   │   ├── audit_runner.py
│   │   ├── extended_audit_runner.py
│   │   ├── integrated_audit_runner.py
│   │   ├── result_processor.py
│   │   ├── violation_categorizer.py
│   │   ├── working_axe_analyzer.py
│   │   ├── __init__.py
│   │   ├── extended_audits/
│   │   │   ├── base_audit.py
│   │   │   ├── extended_audit_runner.py
│   │   │   ├── keyboard_audit.py
│   │   │   ├── landmark_audit.py
│   │   │   ├── screen_reader_audit.py
│   │   │   ├── skip_link_audit.py
│   │   │   └── __init__.py
│   │   └── models/
│   │       ├── audit_models.py
│   │       ├── extended_audit_models.py
│   │       └── __init__.py
│   │
│   ├── llm/
│   │   ├── groq_client.py
│   │   └── __init__.py
│   │
│   ├── reporting/
│   │   ├── excel_reporter.py
│   │   ├── report_generator.py
│   │   ├── report_writer.py
│   │   └── __init__.py
│   │
│   └── utils/
│       ├── config_manager.py
│       ├── file_utils.py
│       ├── license_manager.py
│       ├── logger.py
│       ├── validators.py
│       └── __init__.py
│
├── storage/
│   ├── crawled_urls.txt
│   ├── logs/
│   │   └── audit_tool.log
│   └── reports/
│
└── tests/
    ├── conftest.py
    └── __init__.py

```

## Create directory
```
.\create_structure.ps1
```
**⚠️ If you get "script execution disabled" error**
```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

🎯 Core Accessibility Analysis Features
1. Standard Axe-Core Analysis
WCAG 2.1 A & AA Compliance - Automated rule checking
Best Practice Rules - Industry-standard accessibility guidelines
Keyboard Accessibility - Focus on keyboard-only users
Time-based Rules - Timing and focus management

2. Unique Productivity-Focused Features (Beyond Standard Tools)
🔍 Navigation Flow Analysis
Skip Links Detection - Checks for "Skip to content" links

Landmark Regions Analysis - <main>, <nav>, <header>, <footer>, <aside>

Focus Management - Focus indicator coverage and visibility

Focusable Elements Tracking - Count and accessibility of focusable elements

🖱️ Interactive Elements Analysis
Form Accessibility:

Label association analysis (for attributes, aria-labelledby)

ARIA attribute usage (aria-required, aria-invalid, aria-describedby)

Form validation accessibility

Button Accessibility:

Accessible name detection (text content, aria-label, title)

Keyboard accessibility status

Interactive state analysis

📝 Content Structure Analysis
Heading Hierarchy:

Proper heading structure (H1-H6)

Hierarchy gap detection (H1 → H3 jumps)

Missing H1 detection

Content Density:

Word count analysis

Paragraph and list structure

Readability scoring

⚡ Performance Impact Analysis
Resource Impact:

Accessibility resource loading (ARIA, a11y scripts)

File size impact of accessibility features

DOM Complexity:

Total elements vs interactive elements ratio

Performance impact assessment

🧠 Cognitive Load Analysis
Language Complexity:

Sentence length analysis

Complex word detection (8+ chars, multiple syllables)

Readability scoring

Visual Complexity:

Structural element counting (sections, containers, modals)

Cognitive overload assessment

🎮 Dynamic Interaction Analysis (NEW - Most Unique Feature)
Button Interaction Testing:

onclick handler analysis

Focus maintenance after clicks

Dynamic content triggering detection

Click timeout and error handling

Form Submission Testing:

HTML5 validation testing

Accessible error message analysis

Submission behavior monitoring

Dynamic Content Monitoring:

AJAX request detection

DOM modification tracking

Modal dialog interaction testing

Tab interface accessibility

Keyboard Navigation Testing:

Tab order analysis

Focus trap detection

Keyboard handler verification

Focus Management Testing:

Focus restoration after interactions

Modal focus trapping

Dynamic focus targeting

ARIA Live Regions Analysis:

Live region detection (aria-live)

Polite vs assertive regions

Content announcement analysis

3. Performance & Technical Features
📊 Performance Metrics
Page Load Timing:

DOM Content Loaded time

Full page load time

First Paint & First Contentful Paint

Resource Monitoring:

Network request tracking

Asset loading performance

🖼️ Visual Analysis
Screenshot Analysis:

Visual change detection

Dynamic content visualization

File size and format analysis

4. Analysis Coordination & Batch Processing
🔄 Batch Analysis Features
Concurrent Processing - Multiple URLs analyzed simultaneously

Resource Management - Controlled browser instances

Error Handling - Individual URL failures don't stop entire process

Progress Tracking - Real-time analysis progress

📈 Comprehensive Reporting
Individual Page Results - Detailed per-URL analysis

Aggregate Summary - Cross-site trends and patterns

Priority Issue Identification - Critical vs minor issues

Performance Benchmarks - Load time and resource metrics

🚀 What Makes This Unique vs Other Tools
✅ Standard Tools Do:
Basic WCAG compliance checking

Color contrast analysis

Alt text verification

Basic ARIA attribute checking

🎯 OUR Tool Does (Beyond Standard):
User Productivity Focus - How accessibility affects task completion time

Dynamic Interaction Testing - Real user interaction simulation

Cognitive Load Analysis - Impact on users with cognitive disabilities

Performance Impact Assessment - How a11y affects page speed

Focus Management Verification - Real keyboard navigation testing

Content Structure Intelligence - Beyond basic heading checks

Batch Processing at Scale - Enterprise-level site analysis

🔬 Advanced Detection Capabilities
Hidden Accessibility Issues - Problems only visible after interaction

Progressive Enhancement - How JavaScript affects accessibility

State Management - Focus and ARIA state changes

Error Recovery - How forms handle invalid input accessibly

Dynamic Content - AJAX-loaded content accessibility