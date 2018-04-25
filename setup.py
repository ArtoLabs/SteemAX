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
        'python-dateutil',
        'steem',
        'pymysql',
    ],
    include_package_data=True,
    zip_safe=False
)

# sudo apt install libssl-dev python-dev
