"""
LuminaOS共享库安装配置
基于现状的简化安装配置，支持本地开发环境
"""

from setuptools import setup, find_packages
import os

# 读取版本信息
def get_version():
    with open("__init__.py", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"\'')
    return "1.0.0"

# 读取README
def get_long_description():
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    return "LuminaOS平台共享库"

# 读取依赖
def get_requirements():
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return [
        "pydantic>=2.0.0",
        "typing-extensions>=4.8.0",
    ]

setup(
    name="shared_libs",
    version=get_version(),
    author="LuminaOS Team",
    author_email="team@luminaos.com",
    description="LuminaOS企业AI平台共享库",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/enterprise-ai-platform",

    # 包配置 - 查找当前目录下的所有包
    packages=find_packages(include=["schemas*", "common*", "src*"]),

    # 包含当前目录作为根包
    py_modules=["__init__"],

    # Python版本要求
    python_requires=">=3.11",

    # 依赖
    install_requires=get_requirements(),

    # 额外依赖（开发用）
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
        ],
    },

    # 分类
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],

    # 包含非Python文件
    include_package_data=True,
    zip_safe=False,
)