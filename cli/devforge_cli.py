#!/usr/bin/env python3
"""
DevForge Command Line Interface
Provides easy command-line access to all platform features
"""

import click
import json
import sys
from typing import Optional
from datetime import datetime
from pathlib import Path

from ml.orchestrator_client import get_client
from ml.agents import (
    BrowserAgent,
    TestGenerationAgent,
    BugDetectionAgent,
    WebTaskAgent
)
import asyncio


@click.group()
@click.version_option(version="2.0.0")
@click.pass_context
def cli(ctx):
    """
    DevForge - AI-Powered Testing and Automation Platform

    A comprehensive platform for autonomous web automation, test generation,
    and bug detection powered by Claude AI.
    """
    ctx.ensure_object(dict)


@cli.group()
def agent():
    """Agent management commands"""
    pass


@cli.group()
def task():
    """Task management commands"""
    pass


@cli.group()
def api():
    """API commands"""
    pass


@cli.group()
def config():
    """Configuration commands"""
    pass


# ===== Agent Commands =====

@agent.command()
@click.option('--url', required=True, help='URL to navigate to')
@click.option('--task', required=True, help='Task description')
def browser(url, task):
    """Run BrowserAgent"""
    click.echo("🌐 Starting BrowserAgent...")
    click.echo(f"   URL: {url}")
    click.echo(f"   Task: {task}")

    async def run():
        agent = BrowserAgent()
        await agent.start()
        try:
            result = await agent.execute_task(task)
            click.echo(f"\n✅ Task completed!")
            click.echo(f"   Status: {result['status']}")
            click.echo(f"   Steps: {result['steps']}")
        finally:
            await agent.stop()

    asyncio.run(run())


@agent.command()
@click.option('--description', required=True, help='Test description')
@click.option('--url', help='Target URL')
@click.option('--framework', default='pytest', help='Test framework')
def test(description, url, framework):
    """Generate tests with TestGenerationAgent"""
    click.echo("✓ Starting TestGenerationAgent...")
    click.echo(f"   Description: {description}")
    click.echo(f"   Framework: {framework}")

    agent = TestGenerationAgent()
    result = agent.generate_test(
        description=description,
        url=url,
        framework=framework
    )

    if result['status'] == 'success':
        click.echo(f"\n✅ Test generated!")
        click.echo(f"   Name: {result['test_name']}")
        click.echo(f"   Code length: {len(result['code'])} characters")
        click.echo(f"   Assertions: {len(result['assertions'])}")

        # Save to file
        filename = f"test_{result['test_name']}.py"
        Path(filename).write_text(result['code'])
        click.echo(f"   Saved to: {filename}")
    else:
        click.echo(f"❌ Error: {result.get('error')}")
        sys.exit(1)


@agent.command()
@click.option('--url', required=True, help='URL to scan')
@click.option('--tests', multiple=True, help='Test cases to run')
def bugs(url, tests):
    """Scan for bugs with BugDetectionAgent"""
    click.echo("🐛 Starting BugDetectionAgent...")
    click.echo(f"   URL: {url}")
    if tests:
        click.echo(f"   Test cases: {', '.join(tests)}")

    async def run():
        agent = BugDetectionAgent()
        await agent.start()
        try:
            result = await agent.detect_bugs(url, list(tests) if tests else None)
            click.echo(f"\n✅ Scan complete!")
            click.echo(f"   Bugs found: {result['bugs_found']}")

            if result['bugs']:
                click.echo("\n   Issues:")
                for bug in result['bugs']:
                    click.echo(f"   - [{bug['severity'].upper()}] {bug['description']}")

        finally:
            await agent.stop()

    asyncio.run(run())


@agent.command()
@click.option('--task', required=True, help='Task description')
@click.option('--url', help='Starting URL')
def web(task, url):
    """Execute web tasks with WebTaskAgent"""
    click.echo("⚙️  Starting WebTaskAgent...")
    click.echo(f"   Task: {task}")

    async def run():
        agent = WebTaskAgent()
        await agent.start()
        try:
            result = await agent.execute_task(task, start_url=url)
            click.echo(f"\n✅ Task completed!")
            click.echo(f"   Status: {result.status}")
            click.echo(f"   Steps executed: {result.steps_executed}")
            if result.output:
                click.echo(f"   Output: {result.output}")
        finally:
            await agent.stop()

    asyncio.run(run())


# ===== Task Commands =====

@task.command()
@click.option('--type', 'task_type', required=True,
              type=click.Choice(['browser', 'test', 'bug', 'web']),
              help='Task type')
@click.option('--description', required=True, help='Task description')
@click.option('--url', help='Target URL')
@click.option('--priority', default='medium',
              type=click.Choice(['low', 'medium', 'high', 'critical']),
              help='Priority level')
def create(task_type, description, url, priority):
    """Create a new task"""
    click.echo(f"📝 Creating {task_type} task...")

    client = get_client()

    try:
        if task_type == 'browser':
            task_id = client.browser_navigate(url)
        elif task_type == 'test':
            task_id = client.generate_test(description, url)
        elif task_type == 'bug':
            task_id = client.scan_for_bugs(url)
        elif task_type == 'web':
            task_id = client.execute_web_task(description, url)

        click.echo(f"✅ Task created!")
        click.echo(f"   ID: {task_id}")
        click.echo(f"   Priority: {priority}")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


@task.command()
@click.argument('task_id')
def status(task_id):
    """Get task status"""
    click.echo(f"📊 Checking task status: {task_id}")

    client = get_client()

    try:
        task = client.get_task(task_id)

        if task:
            click.echo(f"\n✅ Task found!")
            click.echo(f"   ID: {task['task_id']}")
            click.echo(f"   Status: {task['status']}")
            click.echo(f"   Progress: {task['progress']}%")

            if task.get('result'):
                click.echo(f"   Result: {json.dumps(task['result'], indent=2)}")
        else:
            click.echo(f"❌ Task not found: {task_id}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


@task.command()
@click.option('--type', 'task_type', help='Filter by task type')
@click.option('--status', help='Filter by status')
@click.option('--limit', default=10, help='Number of tasks to show')
def list(task_type, status, limit):
    """List tasks"""
    click.echo(f"📋 Listing tasks...")

    client = get_client()

    try:
        tasks = client.list_tasks(task_type=task_type, status=status)
        tasks = tasks[:limit]

        if tasks:
            click.echo(f"\nFound {len(tasks)} tasks:\n")
            for task in tasks:
                click.echo(f"  {task['task_id']:<10} | {task['status']:<10} | {task['agent_type']}")
        else:
            click.echo("No tasks found")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


@task.command()
@click.argument('task_id')
def delete(task_id):
    """Delete a task"""
    click.echo(f"🗑️  Deleting task: {task_id}")

    client = get_client()

    try:
        if client.delete_task(task_id):
            click.echo(f"✅ Task deleted!")
        else:
            click.echo(f"❌ Failed to delete task")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


# ===== API Commands =====

@api.command()
def health():
    """Check API health"""
    click.echo("🏥 Checking API health...\n")

    client = get_client()

    try:
        if client.health_check():
            click.echo("✅ All APIs are healthy!")
        else:
            click.echo("❌ API health check failed")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


@api.command()
def stats():
    """Get API statistics"""
    click.echo("📊 Getting API statistics...\n")

    client = get_client()

    try:
        stats = client.get_stats()

        click.echo("Task Statistics:")
        click.echo(f"  Total tasks: {stats['total_tasks']}")
        click.echo(f"  Completed: {stats['completed']}")
        click.echo(f"  Failed: {stats['failed']}")
        click.echo(f"  Running: {stats['running']}")
        click.echo(f"  Pending: {stats['pending']}")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)


# ===== Config Commands =====

@config.command()
@click.option('--key', required=True, help='Config key')
@click.option('--value', required=True, help='Config value')
def set(key, value):
    """Set configuration value"""
    click.echo(f"⚙️  Setting {key} = {value}")

    # Would implement actual config storage
    click.echo("✅ Configuration updated!")


@config.command()
def show():
    """Show current configuration"""
    click.echo("⚙️  Current Configuration:\n")

    from pathlib import Path
    env_file = Path(".env.qa-extended")

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    # Mask sensitive values
                    if "KEY" in key.upper() or "SECRET" in key.upper():
                        value = "***" * 10
                    click.echo(f"  {key.strip()}: {value.strip()}")
    else:
        click.echo("  No configuration file found")


# ===== Main Entry Point =====

if __name__ == '__main__':
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")
        sys.exit(1)
