from enum import Enum
from typing import Dict


class WuXing(Enum):
    """五行枚举"""
    WOOD = "Wood"
    FIRE = "Fire"
    EARTH = "Earth"
    METAL = "Metal"
    WATER = "Water"


class EarthlyBranch(Enum):
    """十二地支枚举，映射为0-11的整数值"""
    ZI = (0, "子")
    CHOU = (1, "丑")
    YIN = (2, "寅")
    MAO = (3, "卯")
    CHEN = (4, "辰")
    SI = (5, "巳")
    WU = (6, "午")
    WEI = (7, "未")
    SHEN = (8, "申")
    YOU = (9, "酉")
    XU = (10, "戌")
    HAI = (11, "亥")

    def __init__(self, index: int, chinese_name: str):
        self.index = index
        self.chinese_name = chinese_name

    @property
    def value(self) -> int:
        return self.index


class RoutingMethod(Enum):
    """九宗门事件路由网关枚举"""
    ZEI_KE = "ZeiKe"
    BI_YONG = "BiYong"
    SHE_HAI = "SheHai"
    YAO_KE = "YaoKe"
    MAO_XING = "MaoXing"
    BIE_ZE = "BieZe"
    BA_ZHUAN = "BaZhuan"
    FU_YIN = "FuYin"
    FAN_YIN = "FanYin"


class HeavenlyStem(Enum):
    """十天干枚举，映射为0-9的整数值"""
    JIA = (0, "甲")
    YI = (1, "乙")
    BING = (2, "丙")
    DING = (3, "丁")
    WU = (4, "戊")
    JI = (5, "己")
    GENG = (6, "庚")
    XIN = (7, "辛")
    REN = (8, "壬")
    GUI = (9, "癸")

    def __init__(self, index: int, chinese_name: str):
        self.index = index
        self.chinese_name = chinese_name

    @property
    def value(self) -> int:
        return self.index


# 全局常量字典
EARTHLY_BRANCH_MAPPING: Dict[int, EarthlyBranch] = {
    branch.index: branch for branch in EarthlyBranch
}

WUXING_MAPPING: Dict[str, WuXing] = {
    wuxing.value: wuxing for wuxing in WuXing
}

ROUTING_METHOD_MAPPING: Dict[str, RoutingMethod] = {
    method.value: method for method in RoutingMethod
}

HEAVENLY_STEM_MAPPING: Dict[int, HeavenlyStem] = {
    stem.index: stem for stem in HeavenlyStem
}

# 天干寄宫法则：天干(0-9)映射到静态底层网格(Earth Index 0-11)
STEM_PARASITIC_MAPPING: Dict[int, int] = {
    0: 2,  # Jia(0) -> Yin(2)
    1: 4,  # Yi(1) -> Chen(4)
    2: 5,  # Bing(2) -> Si(5)
    3: 7,  # Ding(3) -> Wei(7)
    4: 5,  # Wu(4) -> Si(5)
    5: 7,  # Ji(5) -> Wei(7)
    6: 8,  # Geng(6) -> Shen(8)
    7: 10, # Xin(7) -> Xu(10)
    8: 11, # Ren(8) -> Hai(11)
    9: 1   # Gui(9) -> Chou(1)
}

# 天干五行属性映射
STEM_WUXING_MAPPING: Dict[int, WuXing] = {
    0: WuXing.WOOD,    # 甲(0) -> 木
    1: WuXing.WOOD,    # 乙(1) -> 木
    2: WuXing.FIRE,    # 丙(2) -> 火
    3: WuXing.FIRE,    # 丁(3) -> 火
    4: WuXing.EARTH,   # 戊(4) -> 土
    5: WuXing.EARTH,   # 己(5) -> 土
    6: WuXing.METAL,   # 庚(6) -> 金
    7: WuXing.METAL,   # 辛(7) -> 金
    8: WuXing.WATER,   # 壬(8) -> 水
    9: WuXing.WATER    # 癸(9) -> 水
}

# 地支五行属性映射
BRANCH_WUXING_MAPPING: Dict[int, WuXing] = {
    11: WuXing.WATER,  # 亥(11) -> 水
    0: WuXing.WATER,   # 子(0) -> 水
    2: WuXing.WOOD,    # 寅(2) -> 木
    3: WuXing.WOOD,    # 卯(3) -> 木
    5: WuXing.FIRE,    # 巳(5) -> 火
    6: WuXing.FIRE,    # 午(6) -> 火
    8: WuXing.METAL,   # 申(8) -> 金
    9: WuXing.METAL,   # 酉(9) -> 金
    4: WuXing.EARTH,   # 辰(4) -> 土
    10: WuXing.EARTH,  # 戌(10) -> 土
    1: WuXing.EARTH,   # 丑(1) -> 土
    7: WuXing.EARTH    # 未(7) -> 土
}


class YinYang(Enum):
    """阴阳极性枚举"""
    YANG = "阳"
    YIN = "阴"


# 天干极性映射：偶数索引为阳，奇数索引为阴
STEM_YINYANG_MAPPING: Dict[int, YinYang] = {
    0: YinYang.YANG,  # 甲(0) -> 阳
    1: YinYang.YIN,   # 乙(1) -> 阴
    2: YinYang.YANG,  # 丙(2) -> 阳
    3: YinYang.YIN,   # 丁(3) -> 阴
    4: YinYang.YANG,  # 戊(4) -> 阳
    5: YinYang.YIN,   # 己(5) -> 阴
    6: YinYang.YANG,  # 庚(6) -> 阳
    7: YinYang.YIN,   # 辛(7) -> 阴
    8: YinYang.YANG,  # 壬(8) -> 阳
    9: YinYang.YIN    # 癸(9) -> 阴
}


# 地支极性映射：偶数索引为阳，奇数索引为阴
BRANCH_YINYANG_MAPPING: Dict[int, YinYang] = {
    0: YinYang.YANG,   # 子(0) -> 阳
    1: YinYang.YIN,    # 丑(1) -> 阴
    2: YinYang.YANG,   # 寅(2) -> 阳
    3: YinYang.YIN,    # 卯(3) -> 阴
    4: YinYang.YANG,   # 辰(4) -> 阳
    5: YinYang.YIN,    # 巳(5) -> 阴
    6: YinYang.YANG,   # 午(6) -> 阳
    7: YinYang.YIN,    # 未(7) -> 阴
    8: YinYang.YANG,   # 申(8) -> 阳
    9: YinYang.YIN,    # 酉(9) -> 阴
    10: YinYang.YANG,  # 戌(10) -> 阳
    11: YinYang.YIN    # 亥(11) -> 阴
}


def is_clashing(attacker: WuXing, defender: WuXing) -> bool:
    """
    判断五行相克关系
    
    Args:
        attacker: 攻击方五行
        defender: 防御方五行
        
    Returns:
        bool: 是否相克
    """
    clash_map = {
        WuXing.METAL: WuXing.WOOD,   # 金克木
        WuXing.WOOD: WuXing.EARTH,   # 木克土
        WuXing.EARTH: WuXing.WATER,  # 土克水
        WuXing.WATER: WuXing.FIRE,   # 水克火
        WuXing.FIRE: WuXing.METAL    # 火克金
    }
    
    return clash_map.get(attacker) == defender