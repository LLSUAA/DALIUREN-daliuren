"""
大六壬十二天将排布系统

根据日干和昼夜判定，在地盘上确定贵人（Noble）起始位置，
然后顺/逆行将十二天将排布于地盘十二宫，最终映射到天盘十二宫。

十二天将序列（固定顺序）：
    贵人 → 螣蛇 → 朱雀 → 六合 → 勾陈 → 青龙
    → 天空 → 白虎 → 太常 → 玄武 → 太阴 → 天后

顺逆规则：
    - 贵人在 亥/子/丑/寅/卯/辰（天门）→ 顺行（index 递增）
    - 贵人在 巳/午/未/申/酉/戌（地户）→ 逆行（index 递减）
"""

from typing import List, Dict
from engine.components.base_comp import OrbitComp


# ═══════════════════════════════════════════
#   十二天将固定序列（贵人起始，不可变更顺序）
# ═══════════════════════════════════════════
TWELVE_GENERALS: List[str] = [
    "贵人",   # 0
    "螣蛇",   # 1
    "朱雀",   # 2
    "六合",   # 3
    "勾陈",   # 4
    "青龙",   # 5
    "天空",   # 6
    "白虎",   # 7
    "太常",   # 8
    "玄武",   # 9
    "太阴",   # 10
    "天后",   # 11
]


# ═══════════════════════════════════════════
#   昼贵人起法 (日干 → 地盘索引)
#   口诀：甲戊庚牛羊, 乙己鼠猴乡, 丙丁猪鸡位,
#         壬癸兔蛇藏, 六辛逢马虎
#   (前半句 = 昼贵, 后半句 = 夜贵)
# ═══════════════════════════════════════════
DAY_GUI_REN: Dict[int, int] = {
    0: 1,   # 甲 → 丑 (牛)
    1: 0,   # 乙 → 子 (鼠)
    2: 11,  # 丙 → 亥 (猪)
    3: 9,   # 丁 → 酉 (鸡)
    4: 1,   # 戊 → 丑 (牛)
    5: 0,   # 己 → 子 (鼠)
    6: 1,   # 庚 → 丑 (牛)
    7: 6,   # 辛 → 午 (马)
    8: 3,   # 壬 → 卯 (兔)
    9: 5,   # 癸 → 巳 (蛇)
}

# ═══════════════════════════════════════════
#   夜贵人起法 (日干 → 地盘索引)
# ═══════════════════════════════════════════
NIGHT_GUI_REN: Dict[int, int] = {
    0: 7,   # 甲 → 未 (羊)
    1: 8,   # 乙 → 申 (猴)
    2: 9,   # 丙 → 酉 (鸡)
    3: 11,  # 丁 → 亥 (猪)
    4: 7,   # 戊 → 未 (羊)
    5: 8,   # 己 → 申 (猴)
    6: 7,   # 庚 → 未 (羊)
    7: 2,   # 辛 → 寅 (虎)
    8: 5,   # 壬 → 巳 (蛇)
    9: 3,   # 癸 → 卯 (兔)
}


class TianJiangSystem:
    """
    十二天将排布系统 —— 无状态纯计算类

    根据日干确定贵人起始地盘宫位，按天门/地户半区判定顺逆方向，
    将十二天将依次排布于地盘十二宫，最后通过天地盘矩阵映射到天盘。
    """

    @staticmethod
    def assign_generals(
        day_stem_index: int,
        is_daytime: bool,
        orbit_matrix: List[OrbitComp]
    ) -> Dict[int, str]:
        """
        将十二天将分配到天盘十二宫

        Args:
            day_stem_index: 日干索引 (0-9, 甲=0,...,癸=9)
            is_daytime: True=白天(昼占), False=夜间(夜占)
            orbit_matrix: 天地盘轨道矩阵 (12个 OrbitComp)

        Returns:
            Dict[int, str]: 键=天盘索引(heaven_index 0-11), 值=天将名称
        """
        # ── Step 1: 根据日干和昼夜确定贵人地盘起始位置 ──
        gui_ren_mapping = DAY_GUI_REN if is_daytime else NIGHT_GUI_REN
        gui_ren_earth = gui_ren_mapping.get(day_stem_index)
        if gui_ren_earth is None:
            raise ValueError(f"无效的日干索引: {day_stem_index} (范围 0-9)")

        # ── Step 2: 判断顺行还是逆行 ──
        #  天门半区 (亥/子/丑/寅/卯/辰) → 顺行
        #  地户半区 (巳/午/未/申/酉/戌) → 逆行
        shun_xing = TianJiangSystem._is_shun_xing(gui_ren_earth)
        step = 1 if shun_xing else -1

        # ── Step 3: 在地盘上排布十二天将 ──
        #  earth_to_general[earth_index] = 天将名称
        earth_to_general: Dict[int, str] = {}
        for i, general_name in enumerate(TWELVE_GENERALS):
            earth_pos = (gui_ren_earth + i * step) % 12
            earth_to_general[earth_pos] = general_name

        # ── Step 4: 映射到天盘 ──
        #  对每个天盘宫位，找到其下方的地盘宫位，取出对应的天将
        heaven_to_general: Dict[int, str] = {}
        for comp in orbit_matrix:
            heaven_to_general[comp.heaven_index] = earth_to_general[comp.earth_index]

        return heaven_to_general

    @staticmethod
    def _is_shun_xing(gui_ren_earth: int) -> bool:
        """
        判断贵人是否顺行

        天门半区 (亥 11, 子 0, 丑 1, 寅 2, 卯 3, 辰 4) → 顺行
        地户半区 (巳 5, 午 6, 未 7, 申 8, 酉 9, 戌 10) → 逆行
        """
        return gui_ren_earth in (11, 0, 1, 2, 3, 4)
