from setuptools import setup, find_packages


def get_version_and_cmdclass(package_path):
    """Load version.py module without importing the whole package.

    Template code from miniver
    """
    import os
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location(
        "version", os.path.join(package_path, "_version.py"))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__version__, module.cmdclass


version, cmdclass = get_version_and_cmdclass("ambvis")

setup(name='ambvis',
      version=version,
      cmdclass=cmdclass,
      packages=find_packages(),
      scripts=['bin/ambvis'],
      install_requires=['Flask==2.0.1', 'pi-plates==7.21', 'six==1.12.0', 'spidev==3.5', 'RPi.GPIO==0.7.0', 'picamerax==21.9.8'],
      author='Jonas Ohlsson',
      author_email='jonas.ohlsson@slu.se',
      description='A visualization platform for (anaerobic) microorganisms',
      url='https://github.com/jonasoh/ambvis',
      include_package_data=True,
      )
