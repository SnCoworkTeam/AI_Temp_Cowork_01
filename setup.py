"""
企业AI平台 - Enterprise AI Platform
项目安装配置文件
用于代码分析工具识别项目结构
"""

from setuptools import setup, find_packages
import os

# 读取版本信息
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "__init__.py")
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"\'')
    return "1.0.0"

# 读取README
def get_long_description():
    readme_file = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_file):
        with open(readme_file, "r", encoding="utf-8") as f:
            return f.read()
    return "企业AI平台 - Enterprise AI Platform"

setup(
    name="enterprise-ai-platform",
    version=get_version(),
    author="Enterprise AI Platform Team",
    author_email="team@enterprise-ai-platform.com",
    description="企业AI平台 - 微服务架构的智能企业应用平台",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/enterprise-ai-platform",
    
    # 包配置 - 查找所有Python包
    packages=find_packages(
        exclude=[
            "tests*",
            "test*",
            "docs*",
            "*.tests",
            "*.test",
            "web-ui*",
            "node_modules*",
            "backups*",
            ".git*",
            ".cursor*",
        ]
    ),
    
    # Python版本要求
    python_requires=">=3.11",
    
    # 分类
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    # 包含非Python文件
    include_package_data=True,
    zip_safe=False,
)




