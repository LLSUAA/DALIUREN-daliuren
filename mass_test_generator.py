import random
import requests
import time
from datetime import datetime, timedelta

API_URL = "http://127.0.0.1:8000/api/deduce"

# 随机生成事件意图
INTENTS = [
    "测算下个月的跨国收购案能否成功", "占卜遗失的加密货币冷钱包能否找回",
    "测算这次突发车祸的伤者能否脱离危险", "占测竞争对手是否窃取了我们的商业机密",
    "询问即将到来的大选能否顺利连任", "占测近期的连环梦境是否预示着危险"
]

def generate_random_datetime():
    # 随机生成 1990 年到 2030 年之间的任意时间
    start_date = datetime(1990, 1, 1)
    end_date = datetime(2030, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    
    # 随机生成小时和分钟
    random_date = random_date.replace(hour=random.randint(0, 23), minute=random.randint(0, 59))
    return random_date.strftime("%Y-%m-%d %H:%M:00")

def run_mass_fuzz_test(num_tests=50):
    print(f"🚀 开启大六壬引擎工业级压力测试... 目标量: {num_tests} 局")
    success_count = 0
    
    for i in range(num_tests):
        payload = {
            "time_str": generate_random_datetime(),
            "longitude": round(random.uniform(73.0, 135.0), 2), # 模拟中国全境经度
            "gender": random.choice(["男", "女"]),
            "birth_year": random.randint(1950, 2010),
            "event_intent": random.choice(INTENTS)
        }
        
        print(f"[{i+1}/{num_tests}] 轰炸时空坐标: {payload['time_str']}, 经度 {payload['longitude']}...")
        
        try:
            response = requests.post(API_URL, json=payload, timeout=10)
            if response.status_code == 200 and response.json().get("success"):
                print("   ✅ 引擎存活，路由计算成功")
                success_count += 1
            else:
                print(f"   ❌ 引擎崩溃！触发盲区: {response.json().get('error')}")
        except Exception as e:
            print(f"   ❌ 网络/服务异常: {e}")
            
        time.sleep(0.5) # 防止把电脑CPU打满
        
    print(f"🎉 压测结束！引擎存活率: {success_count}/{num_tests}")

if __name__ == "__main__":
    run_mass_fuzz_test(50) # 你可以把 50 改成 1000 甚至 10000