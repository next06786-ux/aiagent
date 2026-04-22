@echo off
"E:\devecostudio-windows-6.0.2.640\DevEco Studio\tools\node\node.exe" "E:\devecostudio-windows-6.0.2.640\DevEco Studio\tools\hvigor\bin\hvigorw.js" --mode module -p module=entry@default -p product=default -p requiredDeviceType=phone assembleHap --analyze=normal --parallel --incremental --daemon
