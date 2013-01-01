from setuptools import setup
from __init__ import __version__


setup(name='nanote',
      version=__version__,
      description='nanote terminal note-taking software',
      author='Ben Morris',
      author_email='ben@bendmorris.com',
      url='https://github.com/hourchallenge/nanote',
      packages=['nanote'],
      package_dir={
                'nanote':''
                },
      entry_points={
        'console_scripts': [
            'nanote = nanote.nanote:main',
        ],
      },
      )
