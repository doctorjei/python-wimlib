from setuptools import setup

long_description = """

"""

setup(
        name="python-wimlib",
        version="0.1.2",
        description="Python bindings for wimlib (unofficial)",
        long_description_content_type='text/plain',
        long_description=long_description,
        author="Gideon S. (0xGiddi)",
        author_email="elmocia@gmail.com",
        url="https://github.com/0xgiddi/python-wimlib",
        packages=["wimlib"],
        package_dir={
                "wimlib": "wimlib",
        },
        license="GPLv3",
        install_requires=[
                "cffi>=1.8.2",
        ],
        classifiers=[
                'Intended Audience :: Developers',
        ],
)
