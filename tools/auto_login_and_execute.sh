#!/bin/bash

# 定义需要执行的命令
execute_commands() {
    # 获取当前目录
    cur_dir=$(pwd)
    
    # 将当前的crontab任务列表保存到x-ui.cron文件中
    crontab -l > x-ui.cron

    # 删除包含$enable_str的行
    sed -i "/$enable_str/d" x-ui.cron

    # 检查是否已经存在相同的任务
    if ! grep -q "@reboot cd $cur_dir/x-ui && nohup ./x-ui run > ./x-ui.log 2>&1 &" x-ui.cron; then
        # 添加新的@reboot任务
        echo "@reboot cd $cur_dir/x-ui && nohup ./x-ui run > ./x-ui.log 2>&1 &" >> x-ui.cron
    fi

    # 安装新的crontab任务列表
    crontab x-ui.cron

    # 删除临时文件x-ui.cron
    rm x-ui.cron
}

# 使用sshpass登录并执行命令
sshpass -p '19821124Rl' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -tt womimi@panel15.serv00.com << EOF
    $(typeset -f execute_commands)
    execute_commands
    exit
EOF

echo "命令执行完成，已退出SSH会话"
