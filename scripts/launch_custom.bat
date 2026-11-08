@echo off
call "%~dp0..\run.bat" --vfs "example_vfs" --prompt "student@unix:~$ " --startup "scripts/demo.txt"
