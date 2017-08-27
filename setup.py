from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='rn2483',
      version='0.2',
      description='Library to interface RN2483 LoRa module',
      url='https://github.com/lorenzschmid/pyRN2483',
      author='Lorenz Schmid, Raffael Hochreutener',
      author_email='lorenz.schmid@retrouvailles.ch, raffi.h@bluewin.ch',
      license='MIT',
      packages=['rn2483'],
      install_requires=[
          'pyserial',
          'argparse'
      ],
      scripts=['bin/rn2483'],
      zip_safe=False)
