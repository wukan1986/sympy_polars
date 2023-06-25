import setuptools

with open("README.md", "r", encoding='utf-8') as fp:
    long_description = fp.read()

version = {}
with open("sympy_polars/_version.py", encoding="utf-8") as fp:
    exec(fp.read(), version)

setuptools.setup(
    name="sympy_polars",
    version=version['__version__'],
    author="wukan",
    author_email="wu-kan@163.com",
    description="symbol expression to polars expression tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wukan1986/sympy_polars",
    packages=setuptools.find_packages(),
    install_requires=[
        'sympy',
        'Jinja2',
        'black',
        'polars',
        'loguru',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Intended Audience :: Developers',
    ],
    python_requires=">=3.7",
)
