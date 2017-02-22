from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='PyObjectTree',
      version='0.1',
      description='Simple tree model for python objects',
      long_description=readme(),
      url='None',
      author='Jennifer Holt',
      author_email='jholt1978@gmail.com',
      license='MIT',
      packages=['ObjectTree'],
      install_requires=[
          'pyqtgraph',
      ],
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose'])
