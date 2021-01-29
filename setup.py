import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="geecracker", # Replace with your own username
    version="0.0.2",
    url="https://github.com/xiaminghu/GeetestCracker",
    project_urls={
        "Documentation": "https://github.com/xiaminghu/GeetestCracker",
        "Source": "https://github.com/xiaminghu/GeetestCracker",
        "Tracker": "https://github.com/xiaminghu/GeetestCracker/issues",
    },
    description="A cracker of geetest depends on selenium",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="hugo",
    maintainer="hugo",
    maintainer_email="minghuhugo@163.com",
    license="MIT",
    packages=setuptools.find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    zip_safe=False,
    # entry_points={
    #     "console_scripts": [""]
    # },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['selenium', 'pillow'],
    extra_require={},
)
