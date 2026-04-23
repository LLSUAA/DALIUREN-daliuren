import requests
import json
import time
from typing import List, Dict

# API 接口地址 (确保你的 server.py 正在运行)
API_URL = "http://127.0.0.1:8000/api/deduce"

# ==========================================
# 1. 在这里配置你的“历史已知事件”测试集
# ==========================================
TEST_CASES: List[Dict] = [
    {
        "case_id": "SHAO_001_宅舍 (鬼呼凶宅)",
        "time_str": "2024-04-15 22:30:00",  # 映射干支：己亥日 亥时 (夜占)
        "longitude": 114.3,               # 开封坐标
        "gender": "男",
        "birth_year": 1980,
        "event_intent": "近来家中夜间常发异响，且家人连连生病卧床，测算家宅风水吉凶。",
        "actual_result": "【邵彦和原断】此乃三传皆鬼之'鬼呼课'，且白虎临门。邵公断言：宅下必有伏尸枯骨作祟。后主人掘地三尺，果见无名骸骨，迁葬后家宅遂安。"
    },
    {
        "case_id": "SHAO_002_走失 (婢女逃亡)",
        "time_str": "2023-09-08 08:15:00",  # 映射干支：戊申日 辰时 (昼占)
        "longitude": 114.3,               
        "gender": "男",
        "birth_year": 1975,
        "event_intent": "家中一名重要女佣突然携带财物逃跑，测算往哪个方向逃了，还能否抓获追回？",
        "actual_result": "【邵彦和原断】玄武发用，天后临支。邵公断：此女并未远逃，乃是与家中某男仆私通，藏于宅院附近或邻居空屋中，不出三日必在东南角被擒获。后果然在邻家柴房抓获。"
    },
    {
        "case_id": "SHAO_003_疾病 (膏肓之危)",
        "time_str": "2023-11-22 06:30:00",  # 映射干支：癸卯日 卯时 (昼占)
        "longitude": 114.3,               
        "gender": "女",
        "birth_year": 1960,
        "event_intent": "家母缠绵病榻多日，今日突然昏迷，大夫束手无策，测算生死吉凶。",
        "actual_result": "【邵彦和原断】初传见白虎病符，看似极凶。然邵公断：日干癸水，得长生印绶暗中相救，此乃绝处逢生。断其不死，且指明需往正北方寻一“水傍木”之医者可救。后依言寻医，果然转危为安。"
    },
    {
        "case_id": "SHAO_004_官讼 (沉冤昭雪)",
        "time_str": "2024-01-18 14:20:00",  # 映射干支：辛酉日 未时 (昼占)
        "longitude": 114.3,               
        "gender": "男",
        "birth_year": 1982,
        "event_intent": "被人诬陷贪墨巨款，已入大狱，明日即将会审，测算此案能否洗清冤屈。",
        "actual_result": "【邵彦和原断】朱雀乘凶，官鬼克身。然邵公明察秋毫，见冲破之神暗藏于末传。断言：明日会审必有突发变故（如关键证人翻供或新证物出现），不仅无罪释放，反能令诬告者反坐入狱。后皆应验。"
    },
    {
        "case_id": "SHAO_NEW_005_赴任 (官禄暗耗)",
        "time_str": "2023-10-07 08:30:00",  # 映射干支：戊戌日 辰时
        "longitude": 114.3,               # 开封坐标 (宋代都城周边)
        "gender": "男",
        "birth_year": 1980,
        "event_intent": "测算此次赴任新岗位能否顺利，上任后有何吉凶。",
        "actual_result": "【邵公原断】初传官星发用，必得高升。然末传见玄武克身，断：上任后防手下贪墨陷害。后果然升任，半年后因属下亏空险遭牵连。"
    },
    {
        "case_id": "SHAO_NEW_006_婚姻 (虚耗之局)",
        "time_str": "2023-07-16 14:30:00",  # 映射干支：乙丑日 未时
        "longitude": 114.3,
        "gender": "男",
        "birth_year": 1985,
        "event_intent": "议亲一富家千金，测算此段姻缘能否成婚，婚后家宅如何。",
        "actual_result": "【邵公原断】财爻虽现但落空亡，且干支相交相克。断：此女外表富丽，实则内藏亏空，成婚必不长久，恐因财起讼。后未听劝阻强娶，一年后女家破产，反目休妻。"
    },
    {
        "case_id": "SHAO_NEW_007_疾病 (绝处逢生)",
        "time_str": "2024-01-28 23:30:00",  # 映射干支：庚寅日 子时
        "longitude": 114.3,
        "gender": "男",
        "birth_year": 1965,
        "event_intent": "父亲突发恶疾，高烧昏迷不醒，测算此病生死吉凶。",
        "actual_result": "【邵公原断】白虎临干看似极凶，然日干得长生，且见天医星动。断：当夜子时最险，若得东方木气之药，明晨可救。后急服对症中药，汗出而解，奇迹生还。"
    },
    {
        "case_id": "SHAO_NEW_008_官讼 (反坐之局)",
        "time_str": "2024-03-10 06:30:00",  # 映射干支：癸酉日 卯时
        "longitude": 114.3,
        "gender": "男",
        "birth_year": 1978,
        "event_intent": "因生意纠纷被对家诬告欺诈，面临牢狱之灾，测算能否洗清冤屈。",
        "actual_result": "【邵公原断】朱雀发用，初必受惊受审。然末传子孙爻现，克制官鬼。断：先惊后喜，必有清正之官查明真相，不仅无罪，反坐诬告之人。后历经两月，终得昭雪。"
    },
    {
        "case_id": "SHAO_NEW_009_孕产 (双生惊险)",
        "time_str": "2023-12-05 10:30:00",  # 映射干支：丙午日 巳时
        "longitude": 114.3,
        "gender": "女",
        "birth_year": 1995,
        "event_intent": "妻子临盆在即，然腹痛难忍迟迟未生，大夫说有难产之危，测算母子平安否。",
        "actual_result": "【邵公原断】三传见胎神受冲，且临天后。断：此乃双生子之象（双胞胎），虽有惊险，但母子最终皆安。后果然艰难产下双胞胎男婴，母子俱全。"
    }
]
    

def run_backtest():
    print("="*50)
    print("🚀 启动大六壬引擎自动化回测系统...")
    print("="*50)
    
    success_count = 0
    report_lines = ["# 大六壬回测报告\n"]
    
    for idx, tc in enumerate(TEST_CASES, 1):
        print(f"\n[{idx}/{len(TEST_CASES)}] 正在回测: {tc['case_id']} ...")
        
        # 组装请求 Payload
        payload = {
            "time_str": tc["time_str"],
            "longitude": tc["longitude"],
            "gender": tc["gender"],
            "birth_year": tc["birth_year"],
            "event_intent": tc["event_intent"]
        }
        
        try:
            # 向本地 API 发送 POST 请求
            response = requests.post(API_URL, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                snapshot = data["snapshot"]
                oracle_reading = snapshot.get("oracle_reading", "未生成神谕")
                four_pillars = snapshot.get("spacetime_params", {}).get("four_pillars", {})
                
                # 记录到报告
                report_lines.append(f"## 测试用例: {tc['case_id']}")
                report_lines.append(f"- **占测时间**: {tc['time_str']}")
                report_lines.append(f"- **四柱八字**: {four_pillars.get('year')} {four_pillars.get('month')} {four_pillars.get('day')} {four_pillars.get('hour')}")
                report_lines.append(f"- **占测事由**: {tc['event_intent']}")
                report_lines.append(f"- **【历史真实结果】**: {tc['actual_result']}")
                report_lines.append(f"\n**🤖 引擎神谕解码**:\n```text\n{oracle_reading}\n```\n")
                report_lines.append("---\n")
                
                print("✅ 推演完成！")
                success_count += 1
            else:
                print(f"❌ 引擎返回错误: {data.get('error')}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 请求失败: {e}")
        
        # 停顿 2 秒，防止把大模型 API 接口频率打满限制 (Rate Limit)
        time.sleep(2)

    # 写入报告文件
    report_filename = "回测报告_BacktestReport.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.writelines(report_lines)
        
    print("="*50)
    print(f"🎉 回测结束！成功完成 {success_count}/{len(TEST_CASES)} 个测试。")
    print(f"📄 请查看生成的报告文件: {report_filename}")

if __name__ == "__main__":
    run_backtest()