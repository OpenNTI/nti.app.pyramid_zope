import codecs
from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
        'nti_zpt_render = nti.app.pyramid_zope.z3c_zpt:main',
    ],
    "z3c.autoinclude.plugin": [
        'target = nti.app',
    ],
}

TESTS_REQUIRE = [
    'nti.testing',
    'zope.testrunner',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.app.pyramid_zope',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="Support for a more Zope-like pyramid.",
    long_description=(_read('README.rst') + '\n\n' + _read("CHANGES.rst")),
    license='Apache',
    keywords='pyramid zope',
    classifiers=[
        'Framework :: Pyramid',
        'Framework :: Zope :: 3',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    url="https://github.com/NextThought/nti.app.pyramid_zope",
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti', 'nti.app'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'nti.property',
        'Chameleon',
        'simplejson',
        'six',
        'PyYAML',
        'pyramid',
        'pyramid-chameleon',
        'z3c.pt',
        'z3c.ptcompat',
        'z3c.template',
        'zope.authentication',
        'zope.browserpage',
        'zope.component',
        'zope.configuration',
        'zope.dottedname',
        'zope.i18n',
        'zope.interface',
        'zope.pagetemplate',
        'zope.proxy',
        'zope.publisher',
        'zope.security',
        'zope.traversing',
        'zope.viewlet',
    ],
    extras_require={
        'test': TESTS_REQUIRE,
    },
    entry_points=entry_points,
)
