from setuptools import find_packages, setup

setup(
    name='oraladder',
    version='0.1',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'filelock',
        'flask',
        'numpy',
        'pyyaml',
        'trueskill',
        'pytest',
    ],
    entry_points=dict(
        console_scripts=[
            'ora-ladder = laddertools.ladder:run',
            'ora-mapstool = laddertools.mapstool:run',
            'ora-ragl   = laddertools.ragl:run',
            'ora-replay = laddertools.replay:run',
            'ora-srvwrap  = laddertools.srvwrap:run',
        ],
    ),
)
