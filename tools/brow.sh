#!/bin/bash

# 检查 url.txt 文件是否存在
if [ ! -f "url.txt" ]; then
    echo "url.txt 文件不存在，请确保文件与脚本在同一目录下。"
    exit 1
fi

# 设置 D-Bus 地址
export DBUS_SESSION_BUS_ADDRESS=/dev/null

# 使用 xvfb 运行 Chrome
while IFS= read -r url; do
    if [ ! -z "$url" ]; then
        echo "正在访问 $url ..."
        xvfb-run -a google-chrome --headless --no-sandbox --disable-gpu --disable-dev-shm-usage --remote-debugging-port=9222 "$url"
    fi
done < "url.txt"

echo "浏览完成。"
