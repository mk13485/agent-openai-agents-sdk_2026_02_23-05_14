#!/usr/bin/env python3
"""
Setup verification script for Databricks OpenAI Agents SDK
Checks if all prerequisites and configuration are correct
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def parse_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def check_command(cmd: str, name: str) -> bool:
    """Check if a command exists"""
    if shutil.which(cmd):
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip() or result.stderr.strip()
            print(f"✓ {name} is installed: {version.split()[0] if version else 'version unknown'}")
            return True
        except:
            print(f"✓ {name} is installed")
            return True
    else:
        print(f"✗ {name} is NOT installed")
        return False


def check_env_file() -> tuple[bool, str]:
    """Check if .env file exists and has required variables for configured backend mode."""
    env_path = Path(".env")
    if not env_path.exists():
        print("✗ .env file not found")
        return False, "unknown"

    print("✓ .env file exists")
    env_vars = parse_env_file(env_path)
    backend = (env_vars.get("AGENT_BACKEND", "") or "").strip().lower()
    if backend not in {"databricks", "openai"}:
        backend = "openai" if env_vars.get("OPENAI_API_KEY") else "databricks"

    print(f"✓ Backend mode: {backend}")

    required_vars = ["MLFLOW_TRACKING_URI"]
    missing_required = [k for k in required_vars if not env_vars.get(k)]
    if missing_required:
        print(f"  ⚠ Missing or empty: {', '.join(missing_required)}")

    if backend == "openai":
        has_openai = bool(env_vars.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY"))
        if not has_openai:
            print("  ⚠ OPENAI_API_KEY is missing (required for AGENT_BACKEND=openai)")
        return len(missing_required) == 0 and has_openai, backend

    optional_vars = ["DATABRICKS_CONFIG_PROFILE", "DATABRICKS_HOST", "DATABRICKS_TOKEN"]
    has_auth = any(env_vars.get(var) for var in optional_vars)
    if not has_auth:
        print(f"  ⚠ No authentication configured (need one of: {', '.join(optional_vars)})")

    return len(missing_required) == 0 and has_auth, backend


def check_databricks_auth() -> bool:
    """Check if Databricks authentication is working"""
    try:
        result = subprocess.run(
            ["databricks", "current-user", "me"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # Try to extract username
            import json
            try:
                user_info = json.loads(result.stdout)
                username = user_info.get("userName", "unknown")
                print(f"✓ Databricks authentication working (user: {username})")
                return True
            except:
                print("✓ Databricks authentication working")
                return True
        else:
            print("✗ Databricks authentication failed")
            print(f"  Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Databricks CLI timeout (check network connection)")
        return False
    except Exception as e:
        print(f"✗ Error checking Databricks auth: {e}")
        return False


def check_python_version() -> bool:
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (>= 3.11 required)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (>= 3.11 required)")
        return False


def check_dependencies() -> bool:
    """Check if Python dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import mlflow
        print("✓ Core Python dependencies installed")
        return True
    except ImportError as e:
        print(f"✗ Missing Python dependencies: {e}")
        print("  Run: uv sync")
        return False


def main():
    print("=" * 60)
    print("Databricks Agent Setup Verification")
    print("=" * 60)
    print()

    checks = []

    print("1. Checking Python...")
    checks.append(check_python_version())
    print()

    print("2. Checking prerequisites...")
    checks.append(check_command("uv", "uv"))
    checks.append(check_command("databricks", "Databricks CLI"))
    checks.append(check_command("node", "Node.js"))
    print()

    print("3. Checking configuration...")
    env_ok, backend = check_env_file()
    checks.append(env_ok)
    print()

    if backend == "databricks":
        print("4. Checking Databricks authentication...")
        checks.append(check_databricks_auth())
        print()
    else:
        print("4. Checking OpenAI authentication...")
        if os.getenv("OPENAI_API_KEY"):
            print("✓ OPENAI_API_KEY available in environment")
            checks.append(True)
        else:
            env_path = Path(".env")
            env_vars = parse_env_file(env_path) if env_path.exists() else {}
            has_key = bool(env_vars.get("OPENAI_API_KEY"))
            checks.append(has_key)
            print("✓ OPENAI_API_KEY configured" if has_key else "✗ OPENAI_API_KEY missing")
        print()

    print("5. Checking Python dependencies...")
    checks.append(check_dependencies())
    print()

    print("=" * 60)
    if all(checks):
        print("✓ ALL CHECKS PASSED!")
        print()
        print("You're ready to start the agent:")
        print("  uv run start-app")
    else:
        print("✗ SOME CHECKS FAILED")
        print()
        print("Please fix the issues above and run this script again.")
        print("For help, see QUICKSTART.md")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
