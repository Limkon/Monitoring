import random

def generate_random_cron_expression():
    minute = random.randint(0, 59)
    hour = random.randint(0, 23)
    day_of_month = "*"
    month = "*"
    day_of_week = "*"

    cron_expression = f"{minute} {hour} {day_of_month} {month} {day_of_week}"
    return cron_expression

# 将生成的随机cron表达式设置为环境变量
print(f"GITHUB_EVENT_SCHEDULE={generate_random_cron_expression()}")
