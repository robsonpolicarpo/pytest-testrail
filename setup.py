from setuptools import setup

setup(
    name="pytest_testrail",
    use_scm_version=True,
    description="pytest plugin for Testrail",
    long_description=open("README.rst").read(),
    author="Robson Policarpo",
    author_email="robsonpolicarpo.com",
    url="https://github.com/robsonpolicarpo/pytest-testrail",
    packages=["pytest_testrail", "pytest_testrail.model", "pytest_testrail.ydh"],
    install_requires=[
        "pytest>=4.2",
        "pytest-variables>=1.5.0",
        "gherkin-official>=4.1.0",
        "requests",
    ],
    entry_points={
        "pytest11": [
            "pytest-testrail = pytest_testrail.testrail_api",
        ]
    },
    setup_requires=["setuptools_scm"],
    license="Mozilla Public License 2.0 (MPL 2.0)",
    keywords="py.test pytest qa ",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Utilities",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
