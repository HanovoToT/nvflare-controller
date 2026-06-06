from setuptools import setup, find_packages

setup(
    name="nvflare-controller",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "flask>=2.0",
        "flask-cors>=3.0",
        "requests>=2.25",
    ],
    entry_points={
        "console_scripts": [
            "nvflare-controller=nvflare_controller.app:main",
        ],
    },
    author="HanovoToT",
    description="NVFlare Controller - Independent control panel for NVFlare Dashboard, POC, Server, and Client management",
    long_description=open("README.md").read() if __name__ == "__main__" else "",
    long_description_content_type="text/markdown",
    url="https://github.com/HanovoToT/nvflare-controller",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)