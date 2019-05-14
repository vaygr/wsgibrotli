import setuptools


setuptools.setup(
    name="wsgibrotli",
    version="0.0.4",
    author="Vlad Glagolev",
    author_email="stealth@sourcemage.org",
    description="Brotli compression WSGI middleware",
    long_description="Brotli compression WSGI middleware",
    license='MIT',
    url="https://github.com/vaygr/wsgibrotli",
    packages=setuptools.find_packages(),
    install_requires=['brotli'],
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
