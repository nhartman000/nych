from setuptools import setup, find_packages

setup(
    name="nych",
    version="0.1.0",
    description="NYCH deterministic symbolic overlay and locality framework",
    author="NH",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "matplotlib",
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "nych=nych.cli:main",
        ],
    },
    python_requires=">=3.10",
)
