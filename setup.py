from setuptools import setup, find_packages

setup(
    name="postrendercleaner",
    version="0.1.0",
    description="A tool for cleaning and optimizing post-render artifacts in media production workflows",
    author="DXA Media Team",
    author_email="info@example.com",
    packages=find_packages(where="src"),
    package_dir={"":"src"},
    install_requires=[
        "pyyaml>=6.0",
        "google-cloud-storage>=2.0.0",
        "google-cloud-logging>=3.0.0",
        "click>=8.0.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "postrendercleaner=postrendercleaner.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
)