@echo off
setlocal
cd /d "%~dp0"
set "CSC=%SystemRoot%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%CSC%" (echo .NET Framework C# compiler not found & exit /b 1)
"%CSC%" /nologo /target:exe /platform:anycpu /optimize+ /out:VECTELUM-Setup.exe /resource:vectelum-local.py,vectelum-local.py VectelumSetup.cs
if errorlevel 1 exit /b 1
VECTELUM-Setup.exe --self-test
