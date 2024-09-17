#!/bin/bash

# 检查url.txt文件是否存在
if [ ! -f "url.txt" ]; then
    echo "url.txt 文件不存在，请确保文件与脚本在同一目录下。"
    exit 1
fi

# 自定义 User-Agent 和 Referrer 等请求头
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
referrer="https://www.google.com"

# 循环读取url.txt中的每一个网址
while IFS= read -r url; do
    if [ ! -z "$url" ]; then
        echo "正在访问 $url ..."
        # 使用 curl 发送 GET 请求，增加请求头，并忽略输出
        curl -s -A "$user_agent" -e "$referrer" "$url" -o /dev/null
    fi
done < "url.txt"

echo "浏览完成。"
