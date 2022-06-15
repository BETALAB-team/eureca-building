from setuptools import setup, find_packages

classifiers = [
  'Development Status :: 1 - Planning',
  'Intended Audience :: Education',
  'Operating System :: OS Independent',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3.8'
]

setup(
   name='eureca-building',
   version='0.1.0',
   author='betalab group UNIPD',
   author_email='enrico.prataviera@phd.unipd.it',
   packages=find_packages(),
   scripts=[],
   url='https://github.com/BETALAB-team/eureca-buildings',
   license='LICENSE',
   description='Package to simulate building energy performace with lumped capacitance models',
   long_description=open('README.md').read(),
   install_requires=[
       "numpy",
       "pandas",
       "pytest",
       "matplotlib",
       "scipy",
       "openpyxl",
       "xlrd",
   ],
)