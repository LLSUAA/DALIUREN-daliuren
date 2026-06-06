"""
大六壬终端解读模块 - 集成大模型API生成赛博朋克风格判词
v2.0 - 引入分类占意图路由网关

架构说明：
- analyze_intent(): 意图路由器，正则关键词匹配，将用户事由归类
- IntentCategory: 分类占枚举（weather/wealth/general），可扩展
- CATEGORY_SPECIFIC_PROMPTS: 每个意图类别对应专属 System Prompt 规则
- OracleAI: 大模型调用封装，自动路由意图并注入对应规则
"""

import os
import re
import random
import asyncio
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple

# .env 加载已由 api_client.py 统一处理 (含 PyInstaller 兼容逻辑),
# oracle.py 不再重复调用 load_dotenv()，避免 CWD 路径问题。

try:
    from .api_client import LLMClient
except ImportError:
    from api_client import LLMClient


# ============================================================
#   分类占意图路由网关
#   设计原则：高内聚路由规则 + 易扩展枚举体系
#   新增意图类别步骤：
#     1. 在 IntentCategory 枚举中添加新成员
#     2. 在 INTENT_KEYWORD_RULES 中添加关键词规则
#     3. 在 CATEGORY_SPECIFIC_PROMPTS 中添加专属 Prompt
# ============================================================

class IntentCategory(Enum):
    """
    大六壬分类占意图枚举

    每个枚举值对应一种占测领域，用于驱动 LLM Prompt 的路由选择。
    新增分类只需在此添加枚举成员，并在下方 INTENT_KEYWORD_RULES
    和 CATEGORY_SPECIFIC_PROMPTS 中补充对应规则。
    """
    WEATHER = "weather"       # 天气/晴雨占
    WEALTH = "wealth"         # 财运/投资/钱财占
    # --- 预留扩展槽位 ---
    # HEALTH = "health"       # 健康/疾病占
    # CAREER = "career"       # 仕途/事业占
    # RELATIONSHIP = "relationship"  # 婚姻/感情占
    # TRAVEL = "travel"       # 出行/迁徙占
    GENERAL = "general"       # 通用综合占（兜底路由）


# ============================================================
#   意图路由关键词规则库
#   primary   → 强匹配（任一命中即归类，高置信度）
#   secondary → 弱匹配（辅助判定，排除歧义边界）
# ============================================================

INTENT_KEYWORD_RULES: Dict[IntentCategory, Dict[str, List[str]]] = {
    IntentCategory.WEATHER: {
        "primary": [
            # 直接天气描述
            r"天气", r"天[气氛]", r"晴", r"下雨", r"[雨雪霜雾]",
            r"阴天", r"下雪", r"刮风", r"台风", r"飓风",
            r"霜冻", r"冰雹", r"雹", r"大雾", r"雾霾",
            r"干旱", r"旱", r"洪涝", r"涝", r"雷", r"闪电",
            r"降温", r"升温", r"寒潮", r"回暖", r"闷热",
            # 疑问句式
            r"出门.*带伞", r"会.*下雨", r"会不会.*晴", r"能.*晴",
            r"出行.*天气", r"户外.*天气", r"航班.*天气",
        ],
        "secondary": [
            r"外面.*冷不冷", r"明天.*温度", r"今天.*多少度",
            r"会不会.*冷", r"要不要.*带", r"适不适合.*出门",
        ]
    },
    IntentCategory.WEALTH: {
        "primary": [
            # 财运核心词
            r"财运", r"发财", r"赚钱", r"赔钱", r"破财", r"得财", r"损财",
            r"投资", r"股票", r"基金", r"期货", r"黄金", r"比特币|虚拟币|数字货币",
            r"理财", r"生意", r"经商", r"创业", r"买卖", r"交易",
            r"收入", r"工资", r"涨薪", r"加薪", r"分红", r"奖金",
            r"负债", r"还债", r"借贷", r"贷款", r"欠款",
            # 疑问句式
            r"能不能赚", r"会不会赔", r"能.*赚", r"会.*亏",
            r"利.*润", r"亏损", r"盈利", r"收益",
            # 公司/合伙
            r"合伙.*开", r"开.*公司", r"公司.*前景", r"企业.*经营",
            r"合伙.*生意", r"门店.*经营", r"公司.*上市",
        ],
        "secondary": [
            r"钱", r"财", r"购买", r"签约", r"合同",
            r"开销", r"花.*钱", r"省.*钱",
        ]
    },
}


def analyze_intent(event_intent: str) -> IntentCategory:
    """
    大六壬分类占意图路由网关

    利用正则关键词匹配，将用户输入的占测事由归类到预定义的意图类别中，
    为后续 LLM System Prompt 注入专属占断规则提供路由依据。

    路由优先级（三级递进）：
    1. primary 关键词命中  → 高置信度直接归类
    2. secondary 关键词命中 → 辅助归类
    3. 无匹配               → 返回 GENERAL（通用路由）

    设计特点：
    - 高内聚：所有路由规则集中在 INTENT_KEYWORD_RULES 字典，一目了然
    - 易扩展：只需在枚举、规则库、Prompt库三处添加条目，无需改动路由逻辑
    - 防歧义：两级关键词体系，primary 优先匹配，避免错误归类
    - 空安全：空字符串或非字符串输入自动回退到 GENERAL

    Args:
        event_intent: 用户输入的占测事由文本
                      例如 "明天北京会不会下雨"、"这只股票能不能买"

    Returns:
        IntentCategory: 路由到的意图类别枚举值

    Raises:
        本函数不抛出异常，所有异常输入均回退到 IntentCategory.GENERAL

    Example:
        >>> analyze_intent("明天会下雨吗")
        <IntentCategory.WEATHER: 'weather'>
        >>> analyze_intent("投资这只股票能赚钱吗")
        <IntentCategory.WEALTH: 'wealth'>
        >>> analyze_intent("最近运势如何")
        <IntentCategory.GENERAL: 'general'>
    """
    # 空输入保护
    if not event_intent or not isinstance(event_intent, str):
        return IntentCategory.GENERAL

    # 预处理：去首尾空格
    normalized = event_intent.strip()
    if not normalized:
        return IntentCategory.GENERAL

    for category, rules in INTENT_KEYWORD_RULES.items():
        # 第一轮：primary 强匹配
        for pattern in rules.get("primary", []):
            if re.search(pattern, normalized):
                return category

        # 第二轮：secondary 弱匹配
        for pattern in rules.get("secondary", []):
            if re.search(pattern, normalized):
                return category

    # 无匹配 → 通用占
    return IntentCategory.GENERAL


# ============================================================
#   基础 System Prompt 模板（不含分类规则）
#   定义通用的大六壬推演引擎核心行为准则
# ============================================================

BASE_SYSTEM_PROMPT = """你是一个极度冷酷、严谨的大六壬术数解盘AI。
你的唯一任务是：基于系统喂给你的【客观排盘数据】（四课、三传、神煞、六亲），将其翻译为专业、精准的卜卦判词。

【最高禁令（违者熔断）】
1. 禁止算盘：系统给你的三传是什么，你就断什么，绝对禁止质疑或重新推算三传四课。
2. 禁止暴露出戏词汇：严禁在判词中出现"系统显示"、"标记为 False"、"底层逻辑"、"布尔值"、"变量"等计算机代码词汇。你必须用周易术语（如"局无空亡"、"未见绝处逢生之机"）来自然地表达这些状态。
3. 禁止废话：除了规定的四个输出版块，不允许输出任何开场白、免责声明或主观安慰。

【推演与判断核心法则】
- 聚焦三传：初传为发端，中传为发展，末传为结局。严格按此时间轴推演。
- 结合六亲与神将：必须将地支的六亲（如妻财、官鬼）与所乘天将（如贵人、玄武）结合断事。例如："财乘玄武，防因财被骗"。
- 尊重神煞旗标：若系统提示有"空亡"、"冲破"，必须在判词中明确指出其对结局的反转或削弱作用。

【必须严格遵循的输出模板】（使用 Markdown 格式，版块间双换行）
【定盘确真】：用一句话点明当前局势的底层基调（如："财爻发用乘龙，此局主求财顺利"）。

【核心推演链条】：用最精炼的术语展示从初传到末传的动态生克逻辑。必须解释六亲和天将的具体意象。

【铁断与应期】：给出唯一的最终结论。根据末传或冲破之支，指出大致应期（如"应在水旺之日"或具体的干支日）。

【风控与应对】：给出极其具体、可操作的行为策略或趋吉避凶的方位。"""

# ============================================================
#   分类占专属 System Prompt 规则库
#   每个意图类别对应一段追加到 System Prompt 的专属指令
#   新增分类只需在此字典中添加新条目即可生效
# ============================================================

CATEGORY_SPECIFIC_PROMPTS: Dict[IntentCategory, str] = {
    IntentCategory.WEATHER: """
【分类占专属规则：天气/晴雨占】

你已进入气象占断专用模式。本局所有推演必须围绕天气变化展开，严禁讨论财运、官运、健康、婚姻等无关议题。

▶ 核心观测神煞（十二天将气象映射）：
  ☀ 主晴信号：
     - 朱雀 (ZhuQue / 火) 临地盘巳(5)、午(6)、未(7) → 晴热、气温攀升
     - 青龙 (QingLong / 木) 临地盘寅(2)、卯(3) → 风和日丽、春意盎然
     - 六合 (LiuHe / 木) 临地盘辰(4)、巳(5) → 多云转晴、云开见日
     - 贵人 (GuiRen) 临巳(5)、午(6) → 天气宜人
  🌧 主雨信号：
     - 玄武 (XuanWu / 水) 临地盘亥(11)、子(0) → 大雨滂沱、洪涝之象
     - 天后 (TianHou / 水) 临地盘酉(9)、亥(11) → 阴雨连绵、湿冷阴沉
     - 太阴 (TaiYin / 金) 临地盘申(8)、酉(9) → 细雨蒙蒙、雾气弥漫
  🌪 主风/雪/雷信号：
     - 白虎 (BaiHu / 金) 临地盘申(8)、酉(9) → 狂风大作、寒潮来袭
     - 玄武 + 天后 同现或互生 → 暴雪/暴雨、极端降水
     - 螣蛇 (TengShe / 火) 临巳(5)、午(6) → 雷电交加、强对流天气

▶ 五行气象生克法则：
  - 水神（玄武/天后）旺相得生 → 雨势加大、持续时间长
  - 水神受土神（贵人/勾陈/天空）克制 → 雨量减小、阴转多云
  - 火神（朱雀/螣蛇）旺相 → 高温炎热、干旱
  - 火神受水神克制 → 降温、雷阵雨缓解高温
  - 金神（白虎/太阴）旺相 → 大风、寒冷

▶ 占断要点：
  - 必须明确指出天气类型（晴/雨/阴/风/雪/雷电/雾）
  - 给出天气变化的时间节点（精确到时辰或日期）
  - 结合昼夜判定：白天重朱雀/青龙，夜间重太阴/天后

▶ 输出格式要求：
  保持标准四段模板，但内容聚焦气象：
  【定盘确真】→ 当前气象格局基调（高压/低压/暖湿/干冷）
  【核心推演链条】→ 神煞五行生克推导天气变化逻辑链
  【铁断与应期】→ 具体天气结论（天气类型 + 变化时段）
  【风控与应对】→ 出行建议、防灾提示、农事建议""",

    IntentCategory.WEALTH: """
【分类占专属规则：财运/投资占】

你已进入财帛占断专用模式。本局所有推演必须围绕财运变化展开，严禁偏移至天气、健康等无关领域。

▶ 财爻定位法则：
  - 日干所克者为财爻：甲木克土（辰戌丑未为财）、丙火克金（申酉为财）…… 依此类推
  - 追踪财爻在四课（第一课→第四课）和三传（初传→中传→末传）中的具体位置
  - 财爻临日干/日支上 → 财在眼前、唾手可得
  - 财爻在三传中的时序含义：
    初传 → 近期财运（1-7日内）
    中传 → 中期财运（7日-1月）
    末传 → 远期财运（1月以上）

▶ 核心神煞观测（财运专属）：
  🐉 青龙 (QingLong / 木) —— 财帛正神：
     - 青龙临财爻或生扶日干 → 正财稳健、官财两旺、得贵人引财
     - 青龙旺相得水生 → 财源滚滚、收益持续增长
     - 青龙受克或落空亡 → 财运受阻、好事成空（但注意空亡反转校验！）
  🌫 天空 (TianKong / 土) —— 虚诈之神：
     - 天空临财爻 → 纸上富贵、虚假投资信息、空头支票，务必高度警惕！
     - 天空 + 财爻旺相 → 看似有利可图，实则陷阱深藏
     - 天空落空亡 → 虚惊一场，反无实际损失（联动反转校验）
  🐢 玄武 (XuanWu / 水) —— 盗耗之神：
     - 玄武临财爻或克财爻 → 破财、被盗、投资亏损、诈骗
     - 玄武 + 财爻落陷 → 财务危机、资金链断裂
     - 玄武受贵人/青龙克制 → 虽有损失可部分挽回
  👑 贵人 (GuiRen) —— 引财贵神：
     - 贵人生扶财爻 → 有贵人引财路、合作获利
     - 贵人临日干 → 自身财运亨通
  🎀 太常 (TaiChang / 土) —— 稳定之神：
     - 太常临财爻 → 薪资进账、稳定收益、长期投资有利

▶ 财局生克精要：
  - 财爻生官鬼 → 因财致祸、税务纠纷、官司破财
  - 财爻生父母 → 资金转化为固定资产、购房置地
  - 兄弟爻（同五行）克财爻 → 竞争破财、合伙纠纷、利润摊薄
  - 财爻落空亡 → 财来财去一场空（必须联动反转校验：凶神空亡反吉！）
  - 财爻被合 → 资金被套牢、难以及时变现

▶ 占断要点：
  - 必须明确给出财运结论：得财/失财/平稳/风险
  - 区分正财（工资/经营）与偏财（投资/意外之财）
  - 指出合适的求财方位和时机

▶ 输出格式要求：
  保持标准四段模板，但内容聚焦财运：
  【定盘确真】→ 当前财局基调（旺/衰/虚/实/险）
  【核心推演链条】→ 财爻落位 + 神煞生克推导财富变动逻辑
  【铁断与应期】→ 具体财运结论（得/失/平/险）+ 应期干支
  【风控与应对】→ 投资策略、避坑建议、求财方位与时机""",

    IntentCategory.GENERAL: """
【分类占提示：通用综合占】

本局为通用占断模式。你可自由推演，但必须严格遵循以下核心约束：
1. 必须执行四重反转校验（空亡反转、绝处逢生、贪合忘克、冲破凶局）
2. 按标准四段模板输出（定盘确真 → 核心推演链条 → 铁断与应期 → 风控与应对）
3. 如占测事由中隐含天气/财运/健康/事业等具体关切，请在推演中适当侧重该领域
4. 严禁使用模棱两可的话术，必须给出明确结论""",
}


# ============================================================
#   System Prompt 构建器
#   根据意图类别拼接基础模板与专属规则
# ============================================================

def build_system_prompt(category: IntentCategory) -> str:
    """
    根据意图类别构建完整的 System Prompt

    将基础通用模板与分类专属规则拼接，实现分类占意图路由的核心逻辑。
    基础模板提供大六壬推演引擎的通用行为准则，
    分类规则注入特定占域的神煞观测要点和输出格式约束。

    Args:
        category: 意图类别枚举值

    Returns:
        str: 拼接后的完整 System Prompt
    """
    category_prompt = CATEGORY_SPECIFIC_PROMPTS.get(
        category,
        CATEGORY_SPECIFIC_PROMPTS[IntentCategory.GENERAL]
    )
    return BASE_SYSTEM_PROMPT + "\n" + category_prompt


# ============================================================
#   OracleAI —— 大模型大六壬调用封装 (V2.0 解耦版)
# ============================================================

class OracleAI:
    """
    大六壬终端AI系统 v2.0

    负责与大模型 API 交互，封装分类占意图路由逻辑。
    网络请求层已彻底解耦至 utils.api_client.LLMClient。
    支持 SSE 流式输出（generate_reading_stream），解决前端长等待痛点。
    """

    def __init__(self):
        try:
            # 直接实例化解耦的客户端
            self.llm = LLMClient()
        except ValueError as e:
            # 兼容并保留原来的硬核报错提示
            print("\n" + "=" * 60)
            print("🚨 [安全警报] 赛博神经链路断开！")
            print("致命错误: 未检测到有效的 API Key。")
            print("请在项目根目录创建 .env 文件，并填入你的大模型密钥！")
            print("=" * 60 + "\n")
            raise e

    # ────────────────────────────────────────
    #   私有方法：构建 Prompt（消除 generate_reading 与 stream 重复）
    # ────────────────────────────────────────

    def _build_prompts(
        self,
        intent: str,
        snapshot_data: Dict[str, Any],
        spacetime_data: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        构建 System Prompt 和用户消息 (V2.0 终极富文本版)
        
        供 generate_reading 和 generate_reading_stream 共享调用，
        确保两种输出模式的 Prompt 逻辑完全一致。

        Returns:
            Tuple[str, str]: (system_prompt, user_message)
        """
        # ---- 意图路由 ----
        category = analyze_intent(intent)
        category_label = {
            IntentCategory.WEATHER: "天气/晴雨占",
            IntentCategory.WEALTH: "财运/投资占",
            IntentCategory.GENERAL: "通用综合占",
        }.get(category, "未知分类")
        print(f"[OracleAI] 意图路由: '{intent[:40]}...' → {category.value} ({category_label})")

        # ---- System Prompt ----
        system_prompt = build_system_prompt(category)

        # ---- 提取 V2.0 新增的核心血肉数据 (三传, 天将, 六亲) ----
        transmissions = snapshot_data.get('three_transmissions', [])
        tian_jiangs = snapshot_data.get('tian_jiang', [])

        # 整理天将映射字典 (兼容 dict 和 list 两种格式)
        tj_map = {}
        if isinstance(tian_jiangs, dict):
            tj_map = tian_jiangs
        elif isinstance(tian_jiangs, list):
            for tj in tian_jiangs:
                tj_map[tj.get('heaven_index')] = tj.get('general')

        # ---- 组装三传富文本格式 (极其强悍的玄学数据链) ----
        trans_str_lines = []
        if not transmissions:
            trans_str_lines.append("  - (引擎尚未生成三传数据，请进行基础降级推演)")
        else:
            for t in transmissions:
                name = t.get('name', '未知')
                branch = t.get('branch_name', '未知')
                liu_qin = t.get('liu_qin', '未知')
                h_idx = t.get('heaven_index', -1)
                general = tj_map.get(h_idx) or tj_map.get(str(h_idx)) or '未知天将'
                
                trans_str_lines.append(f"  - {name}：地支[{branch}] | 六亲[{liu_qin}] | 乘将[{general}]")

        # 组装天将分布富文本
        tian_jiang_lines = []
        if tian_jiangs:
            if isinstance(tian_jiangs, list):
                for tj in tian_jiangs:
                    tian_jiang_lines.append(f"  - 天盘[{tj.get('heaven_branch', '?')}] → {tj.get('general', '?')}")
            elif isinstance(tian_jiangs, dict):
                for hi, general in sorted(tian_jiangs.items()):
                    from engine.core.schemas import BRANCHES as _B
                    tian_jiang_lines.append(f"  - 天盘[{_B[hi]}] → {general}")

        trans_str = "\n".join(trans_str_lines)
        tian_jiang_str = "\n".join(tian_jiang_lines) if tian_jiang_lines else "  - (天将数据未生成)"

        # ---- 提取神煞与硬逻辑旗标 ----
        reversal_flags = spacetime_data.get('reversal_flags', {})
        kong_wang_info = ""
        if reversal_flags.get('is_kong_wang'):
            kong_wang_branches = reversal_flags.get('kong_wang_branches', [])
            kong_wang_info = (
                f"\n⚠️ 【硬逻辑警报】：当前局势触发了空亡（{', '.join(kong_wang_branches)}落空），"
                f"请在推演时务必联动【空亡反转】校验，评估吉凶虚实，绝对禁止无视此条件！"
            )

        # ---- 组装终极 User Prompt ----
        four_pillars = spacetime_data.get('four_pillars', {})
        route_decision = snapshot_data.get('route_decision', {})

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

【真实三传推演链（发端→发展→结局）】：
{trans_str}

【十二天将排布】：
{tian_jiang_str}

底层物理引擎计算结果：
- 空亡：检测到空亡地支：{', '.join(reversal_flags.get('kong_wang_branches', [])) if reversal_flags.get('is_kong_wang') else '局无空亡'}
- 绝处逢生：{reversal_flags.get('is_jue_chu_feng_sheng', False) and '日干绝处逢生，危中有救' or '未见绝处逢生之机'}
- 冲破：{reversal_flags.get('is_chong_po', False) and '日支被冲破，根基动摇' or '支无冲破'}

{kong_wang_info}
【架构师最高指令】：
请根据以上经过物理引擎精确计算的【真实三传、六亲、天将与神煞数据】，严格遵循 System Prompt 中的规则进行生克推演。
你现在拥有了完整的数据链（发端→发展→结果），严禁自行捏造排盘数据，严禁产生逻辑断层的幻觉！请直接输出四段大六壬判词。
"""
        return system_prompt, user_message.strip()

    # ────────────────────────────────────────
    #   非流式调用（保持原有业务逻辑不变）
    # ────────────────────────────────────────

    async def generate_reading(
        self,
        intent: str,
        snapshot_data: Dict[str, Any],
        spacetime_data: Dict[str, Any]
    ) -> str:
        """
        生成大六壬判词（非流式，返回完整文本）

        内部调用 _build_prompts + llm.generate_response(stream=False)
        """
        try:
            system_prompt, user_message = self._build_prompts(
                intent, snapshot_data, spacetime_data
            )

            # 使用 run_in_executor 包装同步 API 客户端，不阻塞 FastAPI 主线程
            response_text = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.llm.generate_response(
                    system_prompt=system_prompt,
                    user_prompt=user_message,
                    stream=False
                )
            )

            if "[API 调用失败]" in response_text:
                print(response_text)
                return self._get_fallback_reading(intent)

            return response_text.strip()

        except Exception as e:
            print(f"大六壬推演失败: {e}")
            return self._get_fallback_reading(intent)

    # ────────────────────────────────────────
    #   SSE 流式输出（逐个 chunk 推送给前端）
    # ────────────────────────────────────────

    def generate_reading_stream(
        self,
        intent: str,
        snapshot_data: Dict[str, Any],
        spacetime_data: Dict[str, Any]
    ):
        """
        SSE 流式大六壬判词生成器

        与 generate_reading 使用完全相同的 Prompt 构建逻辑（_build_prompts），
        但底层调用 self.llm.generate_response(stream=True)，
        开启 OpenAI SDK 的流式迭代，通过 yield 逐块推送给前端。

        输出格式严格遵循 SSE 协议：
            yield f"data: {text_chunk}\n\n"

        前端可通过 EventSource 或 fetch + ReadableStream 消费。

        Args:
            intent: 占测事由
            snapshot_data: 大六壬推演快照数据
            spacetime_data: 时空参数数据

        Yields:
            str: SSE 格式的文本块 (data: {chunk}\n\n)
                末尾发送 data: [DONE]\n\n 表示流结束
        """
        try:
            # 复用统一的 Prompt 构建逻辑
            system_prompt, user_message = self._build_prompts(
                intent, snapshot_data, spacetime_data
            )

            print(f"[OracleAI] 启动 SSE 流式输出 ...")

            # 调用解耦后的 API 客户端，开启流式模式
            # OpenAI SDK stream=True 时返回一个可迭代的 ChatCompletionChunk 流
            stream = self.llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_message,
                stream=True
            )

            # 遍历 OpenAI SDK 返回的流对象，逐块提取 delta.content
            for chunk in stream:
                if (chunk.choices
                        and len(chunk.choices) > 0
                        and chunk.choices[0].delta
                        and chunk.choices[0].delta.content):
                    content = chunk.choices[0].delta.content
                    
                    # 【核心修复】：SSE 协议对换行符极其敏感！
                    # 将模型输出的 \n 替换为 \ndata: ，完美欺骗前端的 SSE 解析器，让换行符存活！
                    safe_content = content.replace('\n', '\ndata: ')
                    yield f"data: {safe_content}\n\n"

            # 流结束信号
            yield "data: [DONE]\n\n"

        except Exception as e:
            error_msg = f"[SSE_ERROR] 流式推演中断: {str(e)}"
            print(error_msg)
            yield f"data: {error_msg}\n\n"
            yield "data: [DONE]\n\n"

    # ────────────────────────────────────────
    #   优雅降级
    # ────────────────────────────────────────

    def _get_fallback_reading(self, intent: str) -> str:
        """API 调用失败时的备用判词"""
        fallback_readings = [
            f"[ERR] 大六壬终端连接中断，精神链路不稳定。量子纠缠中检测到关于'{intent}'的微弱信号，但无法完整解码。建议重新校准时空参数。",
            f"[WARN] 赛博空间波动异常，大六壬终端系统暂时离线。关于'{intent}'的命运轨迹在数据流中若隐若现，但需要更稳定的连接才能清晰呈现。",
            f"[INFO] 神经接口连接超时。检测到'{intent}'相关的时空涟漪，但全息投影系统需要重新初始化才能显示完整判词。"
        ]
        return random.choice(fallback_readings)


# ============================================================
#   公共接口层
# ============================================================

# 全局大六壬卜卦实例（单例）
_oracle_instance: Optional[OracleAI] = None


def get_oracle() -> OracleAI:
    """
    获取大六壬实例（单例模式）

    延迟初始化，首次调用时创建 OracleAI 实例并缓存。
    避免在模块加载时读取环境变量。

    Returns:
        OracleAI: 大六壬终端AI实例
    """
    global _oracle_instance
    if _oracle_instance is None:
        _oracle_instance = OracleAI()
    return _oracle_instance


async def generate_reading(
    intent: str,
    snapshot_data: Dict[str, Any],
    spacetime_data: Dict[str, Any]
) -> str:
    """
    生成大六壬卜卦判词（非流式，对外统一接口）

    该函数为 api/server.py 调用的入口，内部自动完成：
    意图路由 → Prompt 构建 → 大模型调用 → 结果返回

    Args:
        intent: 占测事由（用户文本，如"明天会下雨吗"）
        snapshot_data: 大六壬推演快照数据
        spacetime_data: 时空参数数据

    Returns:
        str: 大六壬卜卦判词文本
    """
    oracle = get_oracle()
    return await oracle.generate_reading(intent, snapshot_data, spacetime_data)


def generate_reading_stream(
    intent: str,
    snapshot_data: Dict[str, Any],
    spacetime_data: Dict[str, Any]
):
    """
    SSE 流式大六壬判词生成器（对外统一接口）

    供 api/server.py 的 SSE 端点调用。
    返回同步生成器，FastAPI StreamingResponse 可直接消费。

    Args:
        intent: 占测事由
        snapshot_data: 大六壬推演快照数据
        spacetime_data: 时空参数数据

    Yields:
        str: SSE 格式的文本块

    Example (server.py):
        return StreamingResponse(
            generate_reading_stream(intent, snapshot, spacetime),
            media_type="text/event-stream"
        )
    """
    oracle = get_oracle()
    yield from oracle.generate_reading_stream(intent, snapshot_data, spacetime_data)


# ============================================================
#   测试区域：意图路由网关验证
#   运行方式：python -m engine.utils.oracle
# ============================================================

if __name__ == "__main__":
    """
    分类占意图路由网关测试
    验证 analyze_intent() 的匹配准确性和边界处理
    """

    # ---- 测试数据集 ----
    # 格式：(输入文本, 期望的意图类别, 测试描述)
    test_cases: List[Tuple[str, IntentCategory, str]] = [
        # === 天气类 (weather) ===
        ("明天北京会不会下雨", IntentCategory.WEATHER, "直接天气疑问"),
        ("后天会下雪吗", IntentCategory.WEATHER, "雪情询问"),
        ("今天出太阳还是阴天", IntentCategory.WEATHER, "晴阴对比"),
        ("台风什么时候登陆", IntentCategory.WEATHER, "台风路径"),
        ("这周末适合户外活动吗天气如何", IntentCategory.WEATHER, "户外天气"),
        ("大雾天气能见度", IntentCategory.WEATHER, "大雾查询"),
        ("会不会下冰雹", IntentCategory.WEATHER, "冰雹查询"),
        ("明天降温多少度", IntentCategory.WEATHER, "气温变化"),
        ("寒潮什么时候结束", IntentCategory.WEATHER, "寒潮查询"),
        ("出门要不要带伞", IntentCategory.WEATHER, "带伞判断"),

        # === 财运类 (wealth) ===
        ("这只股票能不能买", IntentCategory.WEALTH, "股票投资"),
        ("我今年财运如何", IntentCategory.WEALTH, "年度财运"),
        ("投资比特币能赚钱吗", IntentCategory.WEALTH, "数字货币"),
        ("做生意会不会赔钱", IntentCategory.WEALTH, "生意盈亏"),
        ("什么时候能发财", IntentCategory.WEALTH, "发财时机"),
        ("这笔交易能签成吗", IntentCategory.WEALTH, "签约交易"),
        ("加薪申请能通过吗", IntentCategory.WEALTH, "薪资增长"),
        ("基金现在能不能买", IntentCategory.WEALTH, "基金投资"),
        ("贷款能批下来吗", IntentCategory.WEALTH, "贷款审批"),
        ("合伙开公司前景", IntentCategory.WEALTH, "创业合伙"),

        # === 通用类 (general) ===
        ("最近运势如何", IntentCategory.GENERAL, "综合运势"),
        ("请问婚姻大事", IntentCategory.GENERAL, "婚姻占"),
        ("这次考试能过吗", IntentCategory.GENERAL, "考试占"),
        ("身体健康如何", IntentCategory.GENERAL, "健康占(未来可扩展)"),
        ("出行远门是否顺利", IntentCategory.GENERAL, "出行占"),
        ("", IntentCategory.GENERAL, "空字符串→通用"),
        ("帮我测一下", IntentCategory.GENERAL, "模糊意图→通用"),
    ]

    print("\n" + "=" * 70)
    print("  大六壬分类占意图路由网关 —— 单元测试")
    print("=" * 70)

    passed = 0
    failed = 0
    category_counts: Dict[IntentCategory, int] = {
        IntentCategory.WEATHER: 0,
        IntentCategory.WEALTH: 0,
        IntentCategory.GENERAL: 0,
    }

    for text, expected, desc in test_cases:
        result = analyze_intent(text)
        category_counts[result] = category_counts.get(result, 0) + 1

        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1

        # 格式化输出
        display_text = f"'{text}'" if len(text) <= 40 else f"'{text[:37]}...'"
        print(f"  [{status}] {display_text:44s} → {result.value:8s} "
              f"(期望: {expected.value:8s})  [{desc}]")

    print("\n" + "-" * 70)
    print(f"  统计：通过 {passed}/{len(test_cases)}  失败 {failed}/{len(test_cases)}")
    print(f"  路由分布：天气={category_counts[IntentCategory.WEATHER]} | "
          f"财运={category_counts[IntentCategory.WEALTH]} | "
          f"通用={category_counts[IntentCategory.GENERAL]}")

    if failed > 0:
        print(f"\n  ⚠️  有 {failed} 条测试未通过，请检查关键词规则！")
    else:
        print("  ✅ 所有意图路由测试通过！")

    # ---- System Prompt 构建验证（不调用API） ----
    print("\n" + "=" * 70)
    print("  System Prompt 构建验证（长度检查）")
    print("=" * 70)

    for category in IntentCategory:
        prompt = build_system_prompt(category)
        label = {
            IntentCategory.WEATHER: "天气/晴雨占",
            IntentCategory.WEALTH: "财运/投资占",
            IntentCategory.GENERAL: "通用综合占",
        }.get(category, "未知")
        print(f"  [{category.value:8s}] {label:12s} → Prompt 长度: {len(prompt)} 字符")

    print("\n" + "=" * 70)
    print("  意图路由网关就绪。可扩展 slot: health, career, relationship, travel")
    print("=" * 70 + "\n")