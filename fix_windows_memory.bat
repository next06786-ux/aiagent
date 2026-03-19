@echo off
echo ========================================
echo   修复Windows虚拟内存问题
echo   解决FAISS "页面文件太小" 错误
echo ========================================
echo.
echo 这个脚本将帮助你增加Windows虚拟内存
echo.
echo 请按照以下步骤操作：
echo.
echo 1. 右键点击"此电脑" → 属性
echo 2. 点击"高级系统设置"
echo 3. 在"性能"部分点击"设置"
echo 4. 切换到"高级"选项卡
echo 5. 在"虚拟内存"部分点击"更改"
echo 6. 取消勾选"自动管理所有驱动器的分页文件大小"
echo 7. 选择系统盘（通常是C盘）
echo 8. 选择"自定义大小"
echo 9. 设置：
echo    - 初始大小：16384 MB (16 GB)
echo    - 最大大小：32768 MB (32 GB)
echo 10. 点击"设置"，然后"确定"
echo 11. 重启电脑使设置生效
echo.
echo ========================================
echo   或者使用PowerShell自动设置（需要管理员权限）
echo ========================================
echo.
pause
echo.
echo 正在尝试自动设置虚拟内存...
echo.

powershell -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command \"$cs = Get-WmiObject -Class Win32_ComputerSystem; $cs.AutomaticManagedPagefile = $false; $cs.Put(); $pg = Get-WmiObject -Class Win32_PageFileSetting; if ($pg) { $pg.Delete() }; $pg = ([wmiclass]\"Win32_PageFileSetting\").CreateInstance(); $pg.Name = \"C:\\pagefile.sys\"; $pg.InitialSize = 16384; $pg.MaximumSize = 32768; $pg.Put(); Write-Host \"虚拟内存设置成功！请重启电脑。\" -ForegroundColor Green\"' -Verb RunAs"

echo.
echo 如果自动设置失败，请手动按照上述步骤操作
echo.
pause
