from setuptools import setup, find_packages

setup(
    name="rds-mcp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "mcp-server==0.1.4",
        "boto3==1.40.0",
        "anyio==4.5.0",
        "litellm==1.75.0",
        "backoff==2.2.0",
    ],
    extras_require={
        "dev": [
            "pytest==8.3.4",
            "black==25.1.0",
            "isort==6.0.0",
            "ruff==0.9.4",
            "build==1.1.0",
            "twine==6.1.0",
        ],
    },
    entry_points={
        'console_scripts': [
            'rds-mcp=rds_mcp.cli:main',  # This assumes you have a cli.py with a main() function
        ],
    },
    python_requires=">=3.8",
    author="RDS MCP Contributors",
    author_email="neoai.agent@gmail.com",
    description="A Model-Controlled Panel for managing Amazon RDS instances",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/neoai-agent/rds-mcp",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
) 