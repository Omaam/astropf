"""Setup.
"""
from setuptools import find_packages
from setuptools import setup

setup(
    name="astroparticle",
    version="0.0.1",
    description="Xspec inference with particle filter",
    author="Tomoki Omama",
    packages=find_packages(),
    install_requires=[
        "astropy",
        "tensorflow",
        "tensorflow_probability"
    ],
    classifiers=[
        "Development Status :: 1 - Planning"
    ],
)
