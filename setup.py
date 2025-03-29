from setuptools import setup, find_packages

setup(
    name="amplify",
    version="2.1",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-cors",
        "requests",
        "beautifulsoup4",
        "aiohttp",
        "cachetools",
        "python-dotenv",
        "certifi",
    ],
)