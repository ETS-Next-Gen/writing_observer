from setuptools import setup, find_packages

setup(
    name="learning_observer",
    entry_points={
        'console_scripts': [
            'lobserve=learning_observer.run:run'
        ],
    }
)

