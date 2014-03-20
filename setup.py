from setuptools import setup, find_packages
import codecs

VERSION = '0.0.0'

entry_points = {
	'console_scripts': [
		'nti_zpt_render = nti.app.pyramid_zope.z3c_zpt:main',
	]
}

setup(
    name = 'nti.app.pyramid_zope',
    version = VERSION,
    author = 'Jason Madden',
    author_email = 'jason@nextthought.com',
    description = "Support for a more Zope-like pyramid.",
    long_description = codecs.open('README.rst', encoding='utf-8').read(),
    license = 'Proprietary',
    keywords = 'pyramid zope',
    #url = 'https://github.com/NextThought/nti.nose_traceback_info',
    classifiers = [
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
		'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Testing'
		'Framework :: Pyramid',
        ],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti', 'nti.app'],
	install_requires=[
		'setuptools',
		'pyramid',
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
