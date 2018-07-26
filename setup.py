from setuptools import setup, find_packages


PACKAGE_NAME = 'rabbit-tools'


setup(
    name=PACKAGE_NAME,
    version="0.1",
    install_requires='pyrabbit',
    packages=find_packages(exclude=('*.pyc',)),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'rabdel = rabbit_tools.delete:main',
            'rabpurge = rabbit_tools.purge:main',
            'rabbit_tools_config = rabbit_tools.config:main',
            'testone = rabbit_tools.delete:main',
            'testtwo = rabbit_tools.delete:main',
        ],
    },
)
