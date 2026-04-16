from pathlib import Path

from setuptools import find_namespace_packages, setup


ROOT = Path(__file__).resolve().parent
long_description = (ROOT / "README.md").read_text(encoding="utf-8")
requirements = ["regex>=2022.8.17", "xmlschema"]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


setup(
    name="choppa",
    version=version,
    description="A Python port of the Java SRX segmenter library for rule-based text tokenization.",
    python_requires=">=3.7",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dmitro Chaplynskyi",
    author_email="chaplinsky.dmitry@gmail.com",
    url="https://github.com/lang-uk/choppa",
    packages=find_namespace_packages(include=["choppa*"]),
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords="sentence tokenizer,natural language processing,srx",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries",
        "Typing :: Typed",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Natural Language :: Ukrainian",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    package_data={"choppa": ["data/srx/*.srx", "data/xsd/*.xsd"]},
)
