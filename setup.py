from distutils.core import setup

setup(
    name='SteemAX',
    version='0.1',
    packages=['steemax'],
    license='MIT',
    long_description=open('README.txt').read(),
    keywords='funniest joke comedy flying circus',
    url='http://github.com/storborg/funniest',
    author='ArtoLabs',
    author_email='artopium@gmail.com',
    install_requires=[
        'dateutil.parser',
        'datetime',
        'random',
        'steem',
        'steem.converter',
        'steem.amount',
        'steembase.account',
        'steembase.exceptions',
        'cmd',
        're'
    ],
    include_package_data=True,
    zip_safe=False
)
