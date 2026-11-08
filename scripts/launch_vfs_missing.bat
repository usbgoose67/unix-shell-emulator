@echo off
call "%~dp0..\run.bat" --vfs "vfs_examples/missing" --prompt "error$ " --startup "scripts/vfs_demo.txt"
