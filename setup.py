from setuptools import setup, find_packages

setup(
    name='SteemAX',
    version='0.1',
    packages=['steemax'],
    license='MIT',
    long_description=open('README.txt').read(),
    keywords='steemit steem upvote exchange',
    url='http://github.com/artolabs/steemax',
    author='ArtoLabs',
    author_email='artopium@gmail.com',
    install_requires=[
        'python-dateutil',
        'steem',
        'pymysql',
    ],
    scripts = [
        'scripts/steemax.sh'
    ],
    python_requires='>=2.7.12',
    include_package_data=True,
    zip_safe=False
)

# sudo apt install python3 pip libssl-dev python-dev
