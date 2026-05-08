"""
大六壬六亲计算工具

根据日干五行与目标地支五行的生克关系，判定六亲属性。

六亲定义：
    生我者 → 父母      (目标五行生我)
    我生者 → 子孙      (我生目标五行)
    克我者 → 官鬼      (目标五行克我)
    我克者 → 妻财      (我克目标五行)
    同我者 → 兄弟      (五行相同)

五行相生：木→火→土→金→水→木
五行相克：金→木→土→水→火→金
"""

from engine.core.constants import (
    WuXing,
    STEM_WUXING_MAPPING,
    BRANCH_WUXING_MAPPING,
)


# ═══════════════════════════════════════════
#   五行相生映射表 (源五行 → 所生五行)
# ═══════════════════════════════════════════
_WUXING_SHENG_MAP = {
    WuXing.WOOD:  WuXing.FIRE,    # 木生火
    WuXing.FIRE:  WuXing.EARTH,   # 火生土
    WuXing.EARTH: WuXing.METAL,   # 土生金
    WuXing.METAL: WuXing.WATER,   # 金生水
    WuXing.WATER: WuXing.WOOD,    # 水生木
}

# ═══════════════════════════════════════════
#   五行相克映射表 (源五行 → 所克五行)
# ═══════════════════════════════════════════
_WUXING_KE_MAP = {
    WuXing.METAL: WuXing.WOOD,    # 金克木
    WuXing.WOOD:  WuXing.EARTH,   # 木克土
    WuXing.EARTH: WuXing.WATER,   # 土克水
    WuXing.WATER: WuXing.FIRE,    # 水克火
    WuXing.FIRE:  WuXing.METAL,   # 火克金
}


def calculate_liu_qin(day_stem_index: int, target_branch_index: int) -> str:
    """
    计算日干与目标地支之间的六亲关系

    Args:
        day_stem_index: 日干索引 (0-9, 甲=0, 乙=1, ..., 癸=9)
        target_branch_index: 目标地支索引 (0-11, 子=0, ..., 亥=11)

    Returns:
        str: 六亲名称 — "父母" / "子孙" / "官鬼" / "妻财" / "兄弟"

    Raises:
        ValueError: 当日干或目标地支的五行无法解析时
    """
    # ── 获取五行 ──
    day_wuxing = STEM_WUXING_MAPPING.get(day_stem_index)
    if day_wuxing is None:
        raise ValueError(f"无效的日干索引: {day_stem_index} (范围 0-9)")

    target_wuxing = BRANCH_WUXING_MAPPING.get(target_branch_index)
    if target_wuxing is None:
        raise ValueError(f"无效的地支索引: {target_branch_index} (范围 0-11)")

    # ── 同我者兄弟 ──
    if day_wuxing == target_wuxing:
        return "兄弟"

    # ── 生我者父母 (target → day) ──
    if _WUXING_SHENG_MAP.get(target_wuxing) == day_wuxing:
        return "父母"

    # ── 我生者子孙 (day → target) ──
    if _WUXING_SHENG_MAP.get(day_wuxing) == target_wuxing:
        return "子孙"

    # ── 克我者官鬼 (target → day) ──
    if _WUXING_KE_MAP.get(target_wuxing) == day_wuxing:
        return "官鬼"

    # ── 我克者妻财 (day → target) ──
    if _WUXING_KE_MAP.get(day_wuxing) == target_wuxing:
        return "妻财"

    # 理论不应到达这里
    raise RuntimeError(
        f"无法判定六亲: 日干五行={day_wuxing}, 目标五行={target_wuxing}"
    )
