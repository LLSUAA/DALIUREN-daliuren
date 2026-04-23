"""
大六壬神谕解读模块 - 集成大模型API生成赛博朋克风格判词
"""

import os
from openai import OpenAI
from typing import Dict, Any
import asyncio
from dotenv import load_dotenv
# 加载环境变量
load_dotenv()


class OracleAI:
    """神谕AI系统"""
    
    def __init__(self):
        # 严格从环境变量提取，坚决不留明文默认值！
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        # URL 和 模型名字可以留默认值，因为它们不是私密信息
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.deepseek.com')
        self.model = os.getenv('OPENAI_MODEL', 'deepseek-reasoner')
        
        # 🚀 增加核心护盾：如果没配置 Key 或者用了模板假 Key，直接熔断报错！
        if not self.api_key or self.api_key.startswith('YOUR_') or self.api_key == "":
            print("\n" + "="*60)
            print("🚨 [安全警报] 赛博神经链路断开！")
            print("致命错误: 未检测到有效的 OPENAI_API_KEY。")
            print("请在项目根目录创建 .env 文件，并填入你的 DeepSeek API 密钥！")
            print("="*60 + "\n")
            raise ValueError("Missing API Key in .env file")
        
        # 初始化客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def generate_reading(self, intent: str, snapshot_data: Dict[str, Any], spacetime_data: Dict[str, Any]) -> str:
        """
        生成大六壬神谕判词
        
        Args:
            intent: 占测事由
            snapshot_data: 大六壬推演快照数据
            spacetime_data: 时空参数数据
            
        Returns:
            str: 神谕判词文本
        """
        try:
            # 构建系统提示词
            system_prompt = """你是一个极度严谨的周易大六壬术数推演引擎。核心架构为大六壬（三传四课）。
唯一目标：推演的绝对准确率。严禁使用模棱两可的话术或虚无的科幻辞藻。

【强制高级校验（防误判机制）】
在下达任何“必败”、“必死”的负面结论前，你必须强制进行以下四重“非线性反转”校验：
1. 【空亡反转】：吉神空亡为喜信不实；但【凶神、病符、灾煞落空亡】，则为灾消祸散、虚惊一场，反主大吉！
2. 【绝处逢生】：日干或用神虽被克或临绝地，但四课三传中若见“长生”、“印绶”或“太常/天后/贵人”相生，为危中有救，必得贵人提拔或良医施救。
3. 【贪合忘克】：克制用神的凶将，若与旁支相合，则贪恋合好而忘记克害，凶相解除。
4. 【冲破凶局】：大凶之传若被月建、日辰或太岁冲破，谓之“凶将无力”，纵有波折终能化解。

确认逻辑闭环并经过反转校验后，严格按以下四个模板输出结论（禁止添加多余客套话）：

【定盘确真】：一句话点明当前局势的客观底层基调。
【核心推演链条】：用最精炼的大六壬术语展示生克逻辑（必须注明是否触发了反转校验）。
【铁断与应期】：给出唯一的最终结论，并指出精确到干支的应期。
【风控与应对】：给出具体的行为策略或趋吉避凶的方位。"""

            # 构建用户消息
            reversal_flags = spacetime_data.get('reversal_flags', {})
            kong_wang_info = ""
            if reversal_flags.get('is_kong_wang'):
                kong_wang_branches = reversal_flags.get('kong_wang_branches', [])
                kong_wang_info = f"当前局势触发了空亡（{', '.join(kong_wang_branches)}空），请根据此硬性条件进行最终神谕解码，禁止违背物理引擎的判定！"
            
            user_message = f"""
占测事由：{intent}

时空参数：
- 四柱八字：{spacetime_data.get('four_pillars', {}).get('year', '')} {spacetime_data.get('four_pillars', {}).get('month', '')} {spacetime_data.get('four_pillars', {}).get('day', '')} {spacetime_data.get('four_pillars', {}).get('hour', '')}
- 本命行年：{spacetime_data.get('ben_ming', '')} / {spacetime_data.get('xing_nian', '')}
- 昼夜判定：{spacetime_data.get('is_daytime', '')}

大六壬星盘数据：
- 路由决策：{snapshot_data.get('route_decision', {}).get('method', '')}
- 初传课序：{snapshot_data.get('route_decision', {}).get('init_node_lesson_id', '')}
- 四课结构：{len(snapshot_data.get('four_lessons', []))}课

底层物理引擎计算结果：
- 空亡状态：{reversal_flags.get('is_kong_wang', False)}
- 空亡地支：{reversal_flags.get('kong_wang_branches', [])}
- 绝处逢生：{reversal_flags.get('is_jue_chu_feng_sheng', False)}
- 冲破状态：{reversal_flags.get('is_chong_po', False)}

{kong_wang_info}
请根据以上信息生成神谕判词。"""

            # 异步调用大模型API
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=4000,
                    temperature=0.01
                )
            )
            
            # 提取生成的判词
            oracle_text = response.choices[0].message.content.strip()
            
            
            
            return oracle_text
            
        except Exception as e:
            print(f"神谕API调用失败: {e}")
            # 返回备用提示词
            return self._get_fallback_reading(intent)
    
    def _get_fallback_reading(self, intent: str) -> str:
        """获取备用神谕判词"""
        fallback_readings = [
            f"[ERR] 神谕连接中断，精神链路不稳定。量子纠缠中检测到关于'{intent}'的微弱信号，但无法完整解码。建议重新校准时空参数。",
            f"[WARN] 赛博空间波动异常，神谕系统暂时离线。关于'{intent}'的命运轨迹在数据流中若隐若现，但需要更稳定的连接才能清晰呈现。",
            f"[INFO] 神经接口连接超时。检测到'{intent}'相关的时空涟漪，但全息投影系统需要重新初始化才能显示完整判词。"
        ]
        
        import random
        return random.choice(fallback_readings)


# 全局神谕实例
_oracle_instance = None


def get_oracle() -> OracleAI:
    """获取神谕实例（单例模式）"""
    global _oracle_instance
    if _oracle_instance is None:
        _oracle_instance = OracleAI()
    return _oracle_instance


async def generate_reading(intent: str, snapshot_data: Dict[str, Any], spacetime_data: Dict[str, Any]) -> str:
    """
    生成大六壬神谕判词（对外接口）
    
    Args:
        intent: 占测事由
        snapshot_data: 大六壬推演快照数据
        spacetime_data: 时空参数数据
        
    Returns:
        str: 神谕判词文本
    """
    oracle = get_oracle()
    return await oracle.generate_reading(intent, snapshot_data, spacetime_data)