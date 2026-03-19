@echo off
echo ========================================
echo 完全卸载并重装应用（更新图标）
echo ========================================

echo.
echo [1/3] 卸载旧应用...
hdc shell bm uninstall -n com.visionagent.app

echo.
echo [2/3] 清理缓存...
timeout /t 2 /nobreak >nul

echo.
echo [3/3] 安装新应用...
hdc install harmonyos\entry\build\default\outputs\default\entry-default-signed.hap

echo.
echo ========================================
echo 完成！请检查手机桌面图标
echo ========================================
pause
