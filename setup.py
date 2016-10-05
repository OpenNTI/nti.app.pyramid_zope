from setuptools import setup, find_packages
import codecs

VERSION = '0.0.0'

entry_points = {
	'console_scripts': [
		'nti_zpt_render = nti.app.pyramid_zope.z3c_zpt:main',
	],
	"z3c.autoinclude.plugin": [
		'target = nti.app',
	],
}

setup(
	name='nti.app.pyramid_zope',
	version=VERSION,
	author='Jason Madden',
	author_email='jason@nextthought.com',
	description="Support for a more Zope-like pyramid.",
	long_description=codecs.open('README.rst', encoding='utf-8').read(),
	license='Proprietary',
	keywords='pyramid zope',
	classifiers=[
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Topic :: Software Development :: Production'
		'Framework :: Pyramid',
	],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti', 'nti.app'],
	install_requires=[
		'setuptools',
		'simplejson',
		'PyYAML',
		'pyramid',
		'pyramid-chameleon',
		'z3c.template',
		'z3c.pt',
		'z3c.ptcompat',
		'zope.viewlet',
		'zope.proxy',
		'zope.publisher',
		'zope.i18n',
	],
	entry_points=entry_points
)
