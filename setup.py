from setuptools import setup

setup(name='xiaomi_lightbar_nrf24',
      version='0.1',
      description='Control de Xiaomi Monitor Light Bar with a nRF24 module',
      # url='http://github.com/storborg/funniest',
      author='Alejandro García Lampérez',
      author_email='dr.lamperez@gmail.com',
      license='GPLv3',
      # packages=['xiaomi_lightbar_nrf24'],
      install_requires=[
          'pyrf24',
          'crc',
      ],
      zip_safe=False)
