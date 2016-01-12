from setuptools import setup, find_packages

setup(
    name='django-engagements',
    version=__import__('engagements').__version__,
    description='Django tool for collection engagements (like comments or shares) for social networks.',
    long_description=open('README.rst').read(),
    author='Kirill Bolonkin',
    author_email='bolonkin.kirill@gmail.com',
    url='https://github.com/Core2Duo/django-engagements',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'django-annoying',
        'django-picklefield',
        'django-oauth-tokens>=0.2.2',
        'python-dateutil>=1.5',
        'tweepy',
        'django-twitter-api',
        'django-vkontakte-api>=0.8.2',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
