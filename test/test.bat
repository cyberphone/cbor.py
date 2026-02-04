@echo off
if "%1" == "" goto args_count_wrong
if "%2" == "" goto args_count_ok
:args_count_wrong
echo Missing Python file argument
exit /b 1
:args_count_ok
pushd "%~dp0"
SET PYTHONPATH=..\src
py %1
popd

