@echo off
echo Starting Emulator...
start "" cmd /k "set ANDROID_AVD_HOME=D:\AndroidAVD && "C:\Users\sabah computer\AppData\Local\Android\Sdk\emulator\emulator.exe" -avd pixel_6"

echo Waiting 20 seconds...
timeout /t 20 /nobreak

echo Starting Flask...
start "" cmd /k "cd /d D:\downloads\driver_monitoring-master && python app_bridge.py"

echo Starting Detection...
start "" cmd /k "cd /d D:\downloads\driver_monitoring-master && python dms.py --checkpoint models/model_split.h5"

echo Starting Flutter...
timeout /t 5 /nobreak
start "" cmd /k "set GRADLE_USER_HOME=D:\GradleCache && cd /d D:\flutter_app && C:\flutter\flutter\bin\flutter.bat run -d emulator-5554"

pause