# Accessibility Audit Tool

A powerful, automated accessibility auditing solution designed to crawl websites, analyze pages for WCAG compliance, and generate comprehensive reports with actionable insights. This tool leverages **Playwright** for crawling, **axe-core** for accessibility testing, and **LLM (Large Language Model)** integration for business insights and ROI calculations.

## 🚀 Key Features

*   **Automated Crawling**:
    *   Async crawling using **Playwright** for high performance.
    *   Configurable depth, concurrency, and anti-blocking mechanisms (stealth mode, user-agent rotation).
    *   Sitemap validation and intelligent link discovery.
*   **Accessibility Auditing**:
    *   Powered by **axe-core** (via `axe-playwright-python`).
    *   Supports WCAG 2.0, 2.1 (Level A, AA) and Best Practices.
    *   **Basic Audit**: Fast, standard axe-core checks.
    *   **Comprehensive Audit**: Includes extended tests, content analysis, and performance monitoring.
*   **Advanced Analysis**:
    *   **SEO & Content Checks**: Validates titles, meta descriptions, heading structures, and alt text.
    *   **Performance Monitoring**: Tracks page load times and other performance metrics.
    *   **LLM Integration**: Uses Groq (Llama 3) to provide business insights and calculate the ROI of accessibility improvements.
*   **Reporting**:
    *   Generates detailed **Excel** reports with summary and detailed violation sheets.
    *   JSON output for programmatic integration.
    *   Includes screenshots (configurable) and HTML snippets of violations.

## 📋 Prerequisites

*   **Python 3.8+**
*   **Groq API Key** (for LLM features)

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd accessibility-audit-tool
    ```

2.  **Create a virtual environment**
    ```bash
    python -m venv venv
    
    # Windows
    .\venv\Scripts\activate
    
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements/base.txt
    ```

4.  **Install Playwright browsers**
    ```bash
    playwright install
    ```

## ⚙️ Configuration

The tool is highly configurable via `config/config.yaml` and environment variables.

1.  **Environment Setup**:
    Copy `.env.example` to `.env` and add your API keys:
    ```bash
    cp .env.example .env
    ```
    Update `.env` with your Groq API key:
    ```env
    GROQ_API_KEY=your_api_key_here
    ```

2.  **Config File**:
    Edit `config/config.yaml` to set your target website and audit preferences:
    ```yaml
    website:
      url: "https://your-target-website.com"
      max_pages: 100
    
    axe:
      rules:
        tags: ["wcag2aa", "wcag21aa"]
    
    llm:
      provider: "groq"
      model: "llama3-70b-8192"
    ```

## 🏃‍♂️ Usage

Run the main script to start the audit:

```bash
python main.py
```

You will be prompted to select the audit type:

1.  **Basic Audit**: Runs standard axe-core accessibility checks.
2.  **Comprehensive Audit**: Runs axe-core checks plus extended tests, content analysis, and LLM-based insights.

### Command Line Output
The tool provides real-time progress updates and a summary upon completion:
*   URLs Crawled
*   Pages Audited
*   Overall Accessibility Score
*   Total Violations & Breakdown
*   Paths to generated reports

## 📂 Project Structure

```
accessibility-audit-tool/
├── config/                 # Configuration files (config.yaml)
├── src/
│   ├── analyzer/           # Audit logic (AuditRunner, IntegratedAuditRunner)
│   ├── crawler/            # Playwright crawler implementation
│   ├── llm/                # LLM integration (Groq)
│   ├── reporting/          # Report generation (Excel, JSON)
│   └── utils/              # Helper functions and logging
├── storage/
│   ├── reports/            # Generated audit reports
│   └── logs/               # Application logs
├── requirements/           # Python dependencies
├── main.py                 # Entry point
└── README.md               # Documentation
```

## � Output Reports

Reports are saved in the `storage/reports` directory (configurable).

*   **Excel Report**: Contains multiple sheets:
    *   **Summary**: High-level metrics, scores, and charts data.
    *   **Detailed Violations**: Row-by-row breakdown of every issue found, including selectors, impact, and help URLs.
*   **JSON Report**: Full raw data for integration with other tools.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[MIT License](LICENSE)