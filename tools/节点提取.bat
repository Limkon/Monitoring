@echo off
setlocal enabledelayedexpansion

:: 检查是否有输入文件
if "%~1"=="" (
    echo 请拖放文件到该批处理上运行。
    pause
    exit /b
)

:: 设置输出文件名
set "output_file=output_addresses.txt"
echo 结果保存到 %output_file%
> %output_file% echo 提取的地址:

:: 循环处理txt文件中的每一行
for /f "tokens=*" %%a in (%~1) do (
    set "line=%%a"
    :: 提取 @ 后和 : 前的地址
    for /f "tokens=2 delims=@" %%b in ("!line!") do (
        for /f "tokens=1 delims=:" %%c in ("%%b") do (
            echo %%c >> %output_file%
        )
    )
)

echo 提取完成，结果已保存到 %output_file%
pause
