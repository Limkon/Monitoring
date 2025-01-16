#!/bin/bash

# 定义需要执行的命令
execute_commands() {
    # 获取当前目录
    cur_dir=$(pwd)
    
    # 将当前的crontab任务列表保存到x-ui.cron文件中
    crontab -l > x-ui.cron

    # 删除包含$enable_str的行
    sed -i "" "/$enable_str/d" x-ui.cron

    # 添加新的@reboot任务
    echo "@reboot cd $cur_dir/x-ui && nohup ./x-ui run > ./x-ui.log 2>&1 &" >> x-ui.cron

    # 安装新的crontab任务列表
    crontab x-ui.cron

    # 删除临时文件x-ui.cron
    rm x-ui.cron
}

# 无限循环
while true; do
  # 尝试使用SSH密钥登录服务器并执行命令
  ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -tt womimi@panel15.serv00.com << EOF
    $(typeset -f execute_commands)
    execute_commands
    exit
EOF
  
  # 检查SSH命令的退出状态码
  if [ $? -eq 0 ]; then
    echo "命令执行成功，退出SSH会话"
  else
    echo "无法登录或命令执行失败"
  fi

  # 休眠30天（259200秒）
  sleep 259200
done
