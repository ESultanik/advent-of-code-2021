from setuptools import setup, find_packages

setup(
    name="aoc2021",
    description="Evan Sultanik's Advent of Code 2021",
    url="https://github.com/esultanik/aoc2021",
    author="Evan Sultanik",
    version="1.0",
    packages=find_packages(exclude=['test']),
    python_requires='>=3.9',
    install_requires=["tqdm"],
    entry_points={
        'console_scripts': [
            'aoc2021 = aoc2021.__main__:main'
        ]
    }
)
