from setuptools import setup, find_packages

setup(
    python_requires='>=3.0',
    name='SteemAX',
    version='0.3.3',
    packages=['steemax'],
    license='MIT',
    long_description=open('README.txt').read(),
    keywords='steemit steem upvote exchange',
    url='http://github.com/artolabs/steemax',
    author='ArtoLabs',
    author_email='artopium@gmail.com',
    install_requires=[
        'python-dateutil',
        'simplesteem',
        'screenlogger',
    ],
    py_modules=['steemax'],
    entry_points = {
        'console_scripts': [
            'steemax=steemax.steemax:run',
        ],
    },
    include_package_data=True,
    zip_safe=False
)


