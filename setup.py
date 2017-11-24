
import os
from setuptools import setup, find_packages

from lanbilling_stuff.version import __numeric_version__, __author__, __email__, __license__


class SetupPySpec:

	name = "lanbilling-scripts"
	version = __numeric_version__
	description = "Some scripts for lanbilling"
	keywords = ["lanbilling"]
	url = "https://github.com/a1ezzz/lanbilling-scripts"
	classifiers= [
		"Development Status :: 2 - Pre-Alpha",
		"Environment :: Console",
		"Intended Audience :: Developers",
		"Intended Audience :: Information Technology",
		"Intended Audience :: Telecommunications Industry",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Programming Language :: Python :: 3.4",
		"Programming Language :: Python :: 3.5",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7",
		"Programming Language :: Python :: 3 :: Only",
		"Topic :: Utilities"
	]
	# source - http://pypi.python.org/pypi?%3Aaction=list_classifiers

	zip_safe = False

	@staticmethod
	def require(fname):
		return open(fname).read().splitlines()

	@staticmethod
	def read(fname):
	    return open(os.path.join(os.path.dirname(__file__), fname)).read()

if __name__ == "__main__":
	setup(
		name = SetupPySpec.name,
		version = SetupPySpec.version,
		author = __author__,
		author_email = __email__,
		maintainer = __author__,
		maintainer_email = __email__,
		description = SetupPySpec.description,
		license = __license__,
		keywords = SetupPySpec.keywords,
		url = SetupPySpec.url,
		packages = find_packages(),
		include_package_data = True,
		long_description = SetupPySpec.read('README'),
		classifiers = SetupPySpec.classifiers,
		install_requires = SetupPySpec.require('requirements.txt'),
		zip_safe = SetupPySpec.zip_safe
	)
