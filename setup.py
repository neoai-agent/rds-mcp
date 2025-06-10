from setuptools import setup, find_packages

setup(
    name="rds-mcp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "mcp-server>=0.1.0",
        "boto3>=1.26.0",
        "openai>=1.0.0",
        "anyio>=3.7.0",
        "botocore>=1.29.0",
        "python-dateutil>=2.8.2",
        "structlog>=23.1.0",
        "litellm>=1.45.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "ruff>=0.1.0",
            "build>=1.0.0",
            "twine>=4.0.0",
        ],
    },
    entry_points={
        'console_scripts': [
            'rds-mcp=rds_mcp.cli:main',  # This assumes you have a cli.py with a main() function
        ],
    },
    python_requires=">=3.8",
    author="RDS MCP Contributors",
    author_email="your.email@example.com",
    description="A Model-Controlled Panel for managing Amazon RDS instances",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rds-mcp",
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