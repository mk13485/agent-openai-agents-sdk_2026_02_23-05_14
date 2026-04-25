from setuptools import setup, find_packages

setup(
    name="agent-openai-agents-sdk",
    version="0.1.0",
    packages=find_packages(include=["agents*", "api*", "ui*"]),
    include_package_data=True,
    install_requires=[
        "openai>=1.0",
        "fastapi",
        "uvicorn",
        "gradio",
        "httpx",
        "pytest",
        "python-dotenv",
        "mlflow>=2.0",
        "databricks-openai>=0.9.0",
        "databricks-agents",
    ],
    entry_points={
        "console_scripts": [
            "perfect-agent=agents.perfect_agent.runner:main",
        ]
    },
    package_data={
        "agents.perfect_agent": ["system_prompt.txt"],
    },
)
