from setuptools import setup, find_packages

setup(
    name="discord-stock-monitor",
    version="1.0.0",
    description="AI-powered Discord stock pick monitor with Webull integration",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    package_data={
        "config": ["*.prompt", "*.yaml", "*.yml", "*.json"],
    },
    include_package_data=True,
    install_requires=[
        "discord.py-self>=2.0.0",
        "anthropic>=0.39.0",
        "webull>=0.2.4",
        "python-dotenv>=1.0.0",
        "pyperclip>=1.8.2",
        "plyer>=2.1.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "stock-monitor=src.main:main",
        ],
    },
)
