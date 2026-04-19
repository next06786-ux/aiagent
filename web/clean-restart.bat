@echo off
echo Cleaning Vite cache and restarting...
rmdir /s /q node_modules\.vite 2>nul
echo Cache cleaned!
echo Please restart the dev server manually with: npm run dev
pause
