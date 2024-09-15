#!/bin/bash

# 检查url.txt文件是否存在
if [ ! -f "url.txt" ]; then
    echo "url.txt 文件不存在，请确保文件与脚本在同一目录下。"
    exit 1
fi

# 循环读取url.txt中的每一个网址
while IFS= read -r url; do
    if [ ! -z "$url" ]; then
        echo "正在访问 $url ..."
        # 使用 curl 发送 GET 请求并忽略输出
        curl -s -o /dev/null "$url"
    fi
done < "url.txt"

echo "浏览完成。"
