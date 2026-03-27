import click
import httpx
import time
import json
import sys
from typing import Dict, Any

GATEWAY_URL = "http://127.0.0.1:8000"

@click.group()
def cli():
    """A11ySense AI CLI Tool for Accessibility Audits."""
    pass

@cli.command()
@click.argument('url')
@click.option('--type', 'audit_type', default='comprehensive', help='Audit type: basic or comprehensive')
@click.option('--max-pages', default=10, help='Maximum number of pages to crawl')
@click.option('--max-depth', default=3, help='Maximum crawl depth')
@click.option('--wait', is_flag=True, help='Wait for the audit to complete')
def run(url, audit_type, max_pages, max_depth, wait):
    """Start an accessibility audit for the given URL."""
    payload = {
        "url": url,
        "audit_type": audit_type,
        "max_pages": max_pages,
        "max_depth": max_depth
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{GATEWAY_URL}/start_audit", json=payload)
            response.raise_for_status()
            data = response.json()
            task_id = data["task_id"]
            click.echo(f"Audit started! Task ID: {task_id}")
            
            if wait:
                click.echo("Waiting for audit to complete...")
                while True:
                    status_resp = client.get(f"{GATEWAY_URL}/task/{task_id}")
                    status_resp.raise_for_status()
                    status_data = status_resp.json()
                    status = status_data["status"]
                    
                    if status == "completed":
                        click.echo("\nAudit completed successfully!")
                        click.echo(f"Report Paths: {json.dumps(status_data['report_paths'], indent=2)}")
                        break
                    elif status == "failed":
                        click.echo(f"\nAudit failed: {status_data.get('error', 'Unknown error')}")
                        sys.exit(1)
                    else:
                        click.echo(f"Status: {status}...", nl=False)
                        time.sleep(5)
                        click.echo("\r", nl=False)
    except Exception as e:
        click.echo(f"Error connecting to Gateway at {GATEWAY_URL}: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('task_id')
def status(task_id):
    """Check the status of an audit task."""
    try:
        with httpx.Client() as client:
            response = client.get(f"{GATEWAY_URL}/task/{task_id}")
            response.raise_for_status()
            data = response.json()
            click.echo(json.dumps(data, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
def health():
    """Check the health of the Gateway service."""
    try:
        with httpx.Client() as client:
            response = client.get(f"{GATEWAY_URL}/health")
            response.raise_for_status()
            click.echo(f"Gateway is {response.json()['status']}")
    except Exception as e:
        click.echo(f"Gateway is unreachable: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    cli()
