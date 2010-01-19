from setuptools import setup, find_packages

VERSION = (1, 0, 0)

# Dynamically calculate the version based on VERSION tuple
if len(VERSION)>2 and VERSION[2] is not None:
    str_version = "%d.%d_%s" % VERSION[:3]
else:
    str_version = "%d.%d" % VERSION[:2]

version= str_version

setup(
    name = 'django-bursar',
    version = version,
    description = "bursar",
    long_description = """This is a generic payment system for Django. It is a spin-off project from Satchmo.""",
    author = 'Bruce Kroeze',
    author_email = 'brucek@ecomsmith.com',
    url = 'http://bitbucket.org/bkroeze/django-bursar/',
    license = 'New BSD License',
    platforms = ['any'],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Framework :: Django'],
    packages = find_packages(),
    include_package_data = True,
)
