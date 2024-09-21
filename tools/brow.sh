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
        
        # 使用 timeout 包装 Chrome 命令
        {
            timeout 30 xvfb-run --server-args="-screen 0 1280x1024x24" google-chrome --headless --no-sandbox --disable-gpu --disable-dev-shm-usage --remote-debugging-port=9222 "$url" &> chrome_log.txt
        } && {
            echo "访问 $url 成功！"
        } || {
            echo "访问 $url 失败或超时！查看 chrome_log.txt 以获取更多信息。"
        }
    fi
done < "url.txt"

echo "浏览完成。"
