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
    # 清理 URL
    url=$(echo "$url" | tr -d '\r' | tr -d '\n')

    if [ ! -z "$url" ]; then
        echo "正在访问 '$url' ..."

        # 测试 DNS 解析
        if nslookup "$url"; then
            echo "DNS 解析成功，开始访问..."
            # 测试访问 URL
            if curl -Is "$url" | head -n 1 | grep "HTTP/"; then
                echo "URL 可达，开始访问..."
                {
                    timeout 8 xvfb-run google-chrome --headless --no-sandbox --disable-gpu --disable-dev-shm-usage "$url" &> chrome_log.txt
                } && {
                    echo "访问 $url 成功！"
                } || {
                    echo "访问 $url 失败或超时！查看 chrome_log.txt 以获取更多信息。"
                }
            else
                echo "无法访问 $url，可能是网络问题。"
            fi
        else
            echo "DNS 解析失败，无法访问 $url。"
        fi
    fi
done < "url.txt"

echo "浏览完成。"
