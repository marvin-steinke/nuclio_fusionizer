from setuptools import setup, find_packages

setup(
    name="nuclio_fusionizer",
    version="0.1.0",
    author="Marvin Steinke",
    author_email="marvin.steinke@mail.de",
    description="The Nuclio Fusionizer streamlines FaaS tasks into single, cost-effective Nuclio Functions for optimal serverless computing.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=open("requirements.txt").read().splitlines(),
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "nuclio_fusionizer = nuclio_fusionizer.main:main"
        ]
    }
)
