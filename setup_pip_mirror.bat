@echo off
REM 配置 pip 国内镜像源
REM Windows 用户运行此脚本

setlocal enabledelayedexpansion

echo.
echo ================================================================
echo   Configure pip with Chinese Mirror
echo ================================================================
echo.

REM 创建 pip 配置目录
set PIP_CONFIG_DIR=%APPDATA%\pip
if not exist "%PIP_CONFIG_DIR%" (
    mkdir "%PIP_CONFIG_DIR%"
    echo [OK] Created pip config directory: %PIP_CONFIG_DIR%
)

REM 创建 pip.ini 文件
set PIP_CONFIG_FILE=%PIP_CONFIG_DIR%\pip.ini

echo Creating pip.ini...
(
    echo [global]
    echo index-url = https://pypi.tsinghua.edu.cn/simple
    echo extra-index-url = https://mirrors.aliyun.com/pypi/simple/
    echo [install]
    echo trusted-host = pypi.tsinghua.edu.cn
    echo timeout = 120
) > "%PIP_CONFIG_FILE%"

echo [OK] pip.ini created at: %PIP_CONFIG_FILE%
echo.
echo Configuration:
echo   Primary Mirror: Tsinghua University (清华大学)
echo   Backup Mirror: Aliyun (阿里云)
echo   Timeout: 120 seconds
echo.
echo Now you can install packages faster:
echo   pip install -r requirements.txt
echo.
pause










