import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import DaLiuRenEngine


def main():
    """
    大六壬物理引擎沙盒测试脚本
    模拟赛博道观占卜场景，并构建LLM Prompt
    """
    print("=== 大六壬物理引擎沙盒测试 ===")
    print("场景：赛博道观风险评估")
    print("参数：占时巳(5)，月将戌(10)，日干甲(0)，日支寅(2)")
    print()
    
    # 调用引擎生成快照
    try:
        snapshot = DaLiuRenEngine.generate_snapshot(
            zhan_shi_index=5,   # 巳
            yue_jiang_index=10, # 戌
            day_stem_index=0,   # 甲
            day_branch_index=2  # 寅
        )
        
        print("[SUCCESS] 引擎调用成功")
        print()
        
        # 打印JSON快照
        print("=== 推演快照 (JSON格式) ===")
        snapshot_json = json.dumps(snapshot, indent=2, ensure_ascii=False)
        print(snapshot_json)
        print()
        
        # 验证快照结构
        if DaLiuRenEngine.validate_snapshot(snapshot):
            print("[SUCCESS] 快照结构验证通过")
        else:
            print("[ERROR] 快照结构验证失败")
            return
        
        print()
        
        # 构建LLM Prompt
        prompt_template = """
你现在是"灵枢系统"——一个运行在赛博朋克都市废墟中的高维推演协议接口。
用户向你提交了一个风险评估请求。
底层物理引擎传回的推演快照如下：
{snapshot_json}

请遵循以下规则进行渲染解答：
1. 将"orbit_matrix"描述为"近地轨道防御网络阵列"。
2. 将"four_lessons"描述为"四个关键进程锚点"。
3. 解读"route_decision"：
   - 如果 method 是 ZeiKe（贼克），说明系统内部出现异常抛出（底层逻辑叛变）。
   - 如果 method 是 BiYong / SheHai（比用/涉害），说明遭到了并发的外部流量攻击，系统正在进行极性过滤熔断。
4. 必须指出哪个进程锚点（init_node_lesson_id）是引发崩溃的源头。
5. 语调冷峻、机械、带有故障艺术感（Glitch）。字数控制在 250 字以内。不要解释你的推理过程，直接输出警告终端的文本。
"""
        
        # 格式化Prompt
        formatted_prompt = prompt_template.format(snapshot_json=snapshot_json)
        
        print("=== LLM Prompt 模板 ===")
        print(formatted_prompt)
        print()
        
        # 获取快照摘要
        summary = DaLiuRenEngine.get_snapshot_summary(snapshot)
        print("=== 快照摘要 ===")
        print(f"占时索引: {summary['zhan_shi']}")
        print(f"月将索引: {summary['yue_jiang']}")
        print(f"日干索引: {summary['day_stem']}")
        print(f"日支索引: {summary['day_branch']}")
        print(f"路由方法: {summary['route_method']}")
        print(f"初始课序: {summary['init_lesson']}")
        print(f"克战方向: {'下克上' if summary['is_bottom_up'] else '上克下'}")
        
    except Exception as e:
        print(f"[ERROR] 引擎调用失败: {e}")
        return


def test_engine_with_mock_data():
    """
    使用Mock数据测试引擎
    """
    print("\n=== Mock数据测试 ===")
    
    # 测试用例：使用之前创建的Mock数据
    test_cases = [
        {"zhan_shi": 5, "yue_jiang": 10, "day_stem": 0, "day_branch": 2},  # 当前测试用例
        {"zhan_shi": 2, "yue_jiang": 8, "day_stem": 1, "day_branch": 5},  # 其他测试用例
        {"zhan_shi": 0, "yue_jiang": 7, "day_stem": 2, "day_branch": 8}   # 其他测试用例
    ]
    
    for i, case in enumerate(test_cases, 1):
        try:
            snapshot = DaLiuRenEngine.generate_snapshot(
                zhan_shi_index=case["zhan_shi"],
                yue_jiang_index=case["yue_jiang"],
                day_stem_index=case["day_stem"],
                day_branch_index=case["day_branch"]
            )
            
            summary = DaLiuRenEngine.get_snapshot_summary(snapshot)
            print(f"[SUCCESS] 测试用例 {i}: 路由方法={summary['route_method']}, 初始课序={summary['init_lesson']}")
            
        except Exception as e:
            print(f"[ERROR] 测试用例 {i} 失败: {e}")


if __name__ == "__main__":
    # 运行主测试
    main()
    
    # 运行Mock数据测试
    test_engine_with_mock_data()
    
    print("\n=== 测试完成 ===")