from setuptools import setup, find_packages


PACKAGE_NAME = 'rabbit_tools'


setup(
    name=PACKAGE_NAME,
    version="0.1",
    install_requires='pyrabbit',
    packages=find_packages(exclude=('*.pyc',)),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'rabbit_del = rabbit_tools.delete:main',
            'rabbit_purge = rabbit_tools.purge:main',
            'rabbit_tools_config = rabbit_tools.config:create_config_file',
        ],
    },
)
