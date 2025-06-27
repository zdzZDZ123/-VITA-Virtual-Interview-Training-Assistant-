from setuptools import setup, find_packages
import os

# Read version from version.py
version_file = os.path.join(os.path.dirname(__file__), 'version.py')
with open(version_file) as f:
    exec(f.read())

setup(
    name="whisper",
    version=__version__,
    description="Robust Speech Recognition via Large-Scale Weak Supervision",
    author="OpenAI",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "more-itertools",
        "numba",
        "numpy",
        "tiktoken",
        "torch",
        "tqdm",
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'whisper=whisper.transcribe:cli',
        ],
    },
)