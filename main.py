"""
大六壬核心引擎 - 包含神煞与硬逻辑计算
"""

from typing import Dict, Any, List
from engine.systems.astrolabe_sys import AstrolabeSystem
from engine.systems.four_lessons_sys import FourLessonsSystem
from engine.systems.routing_sys import RoutingGatewaySystem
from engine.systems.three_transmissions_sys import ThreeTransmissionsSystem
from engine.systems.tian_jiang_sys import TianJiangSystem
from engine.core.five_elements import calculate_liu_qin
from engine.core.constants import EarthlyBranch, HeavenlyStem
from engine.core.schemas import BRANCHES, STEMS

class DaLiuRenEngine:
    """大六壬核心引擎类"""
    
    @staticmethod
    def generate_snapshot(
        zhan_shi_index: int, 
        yue_jiang_index: int, 
        day_stem_index: int, 
        day_branch_index: int,
        is_daytime: bool = True  # <--- 【核心修复】：必须加上这个参数！
    ) -> Dict[str, Any]:
        """
        生成大六壬推演快照
        """
        # Step 1: 生成天地盘轨道矩阵
        orbit_matrix = AstrolabeSystem.calculate_orbit_matrix(zhan_shi_index, yue_jiang_index)
        
        # Step 2: 生成四课结构
        four_lessons = FourLessonsSystem.extract_lessons(orbit_matrix, day_stem_index, day_branch_index)
        
        # Step 3: 路由决策
        route_decision = RoutingGatewaySystem.dispatch_route(four_lessons, day_stem_index)
        
        # Step 4: 三传推演
        three_transmissions = ThreeTransmissionsSystem.generate_transmissions(
            orbit_matrix, four_lessons, route_decision
        )
        
        # Step 5: 十二天将排布 (这里完美接收并使用了 is_daytime)
        tian_jiang = TianJiangSystem.assign_generals(
            day_stem_index, is_daytime, orbit_matrix
        )
        
        # Step 6: 为三传分别计算六亲
        transmissions_with_liu_qin = []
        for tx in three_transmissions:
            liu_qin = calculate_liu_qin(day_stem_index, tx.heaven_index)
            transmissions_with_liu_qin.append({
                "order": tx.order,
                "name": tx.name,
                "heaven_index": tx.heaven_index,
                "earth_index": tx.earth_index,
                "branch_name": tx.branch_name,
                "liu_qin": liu_qin
            })
        
        # Step 7: 计算神煞与硬逻辑状态
        reversal_flags = DaLiuRenEngine._calculate_reversal_flags(day_stem_index, day_branch_index)
          
        # 组装快照
        snapshot = {
            "orbit_matrix": [
                {
                    "earth_index": comp.earth_index,
                    "heaven_index": comp.heaven_index,
                    "earth_branch": BRANCHES[comp.earth_index],
                    "heaven_branch": BRANCHES[comp.heaven_index]
                }
                for comp in orbit_matrix
            ],
            "four_lessons": [
                {
                    "lesson_id": lesson.lesson_id,
                    "bottom_earth_index": lesson.bottom_earth_index,
                    "top_heaven_index": lesson.top_heaven_index,
                    "bottom_branch": BRANCHES[lesson.bottom_earth_index],
                    "top_branch": BRANCHES[lesson.top_heaven_index]
                }
                for lesson in four_lessons
            ],
            "route_decision": {
                "method": route_decision.route_method.value,
                "init_node_lesson_id": route_decision.init_node_lesson_id,
                "is_bottom_up": route_decision.is_bottom_up
            },
            "three_transmissions": transmissions_with_liu_qin,
            "tian_jiang": [
                {
                    "heaven_index": hi,
                    "heaven_branch": BRANCHES[hi],
                    "general": general_name
                }
                for hi, general_name in sorted(tian_jiang.items())
            ],
            "reversal_flags": reversal_flags
        }
        
        return snapshot
    
    @staticmethod
    def _calculate_reversal_flags(day_stem_index: int, day_branch_index: int) -> Dict[str, Any]:
        """
        计算神煞与硬逻辑状态
        
        Args:
            day_stem_index: 日干索引
            day_branch_index: 日支索引
            
        Returns:
            Dict[str, Any]: 硬逻辑状态字典
        """
        # 计算旬空（空亡）地支
        kong_wang_branches = DaLiuRenEngine._calculate_kong_wang(day_stem_index, day_branch_index)
        
        # 判断是否触发空亡
        is_kong_wang = BRANCHES[day_branch_index] in kong_wang_branches
        
        # 判断是否绝处逢生（简化版，实际需要更复杂的生克计算）
        is_jue_chu_feng_sheng = DaLiuRenEngine._check_jue_chu_feng_sheng(day_stem_index, day_branch_index)
        
        # 判断是否冲破（简化版）
        is_chong_po = DaLiuRenEngine._check_chong_po(day_branch_index)
        
        return {
            "is_kong_wang": is_kong_wang,
            "kong_wang_branches": kong_wang_branches,
            "is_jue_chu_feng_sheng": is_jue_chu_feng_sheng,
            "is_chong_po": is_chong_po
        }
    
    @staticmethod
    def _calculate_kong_wang(day_stem_index: int, day_branch_index: int) -> List[str]:
        """
        计算旬空（空亡）地支 — 基于标准干支数学公式
        
        算法原理：
        六十甲子每旬10组干支，旬首为甲*地支。每旬中缺两个地支，即为空亡。
        
        公式推导：
        1. 旬首地支 = (日支索引 - 日干索引) mod 12
        2. 空亡地支 = (旬首地支 - 2) mod 12, (旬首地支 - 1) mod 12
           
        验证示例：
        - 辛亥日: stem=7(辛), branch=11(亥)
          xun_start = (11-7)%12 = 4(辰) → 甲辰旬
          kong_wang = (4-2)%12=2(寅), (4-1)%12=3(卯) → 寅卯空 ✓
        - 甲子日: stem=0(甲), branch=0(子)
          xun_start = (0-0)%12 = 0(子) → 甲子旬
          kong_wang = (0-2)%12=10(戌), (0-1)%12=11(亥) → 戌亥空 ✓
        
        Args:
            day_stem_index: 日干索引 (0-9)
            day_branch_index: 日支索引 (0-11)
            
        Returns:
            List[str]: 空亡地支列表（两个汉字）
        """
        # 计算旬首地支索引
        xun_start_branch = (day_branch_index - day_stem_index) % 12
        
        # 计算两个空亡地支索引
        kong_wang_1 = (xun_start_branch - 2) % 12
        kong_wang_2 = (xun_start_branch - 1) % 12
        
        return [BRANCHES[kong_wang_1], BRANCHES[kong_wang_2]]
    
    @staticmethod
    def _check_jue_chu_feng_sheng(day_stem_index: int, day_branch_index: int) -> bool:
        """
        判断是否绝处逢生（简化版）
        
        Args:
            day_stem_index: 日干索引
            day_branch_index: 日支索引
            
        Returns:
            bool: 是否绝处逢生
        """
        # 简化逻辑：当日支为日干的绝位，但日干在月将或时支有长生印绶时
        # 这里使用简化判断，实际需要更复杂的生克计算
        
        # 绝位映射：甲绝在申，乙绝在酉，丙绝在亥，丁绝在子，戊绝在亥，
        # 己绝在子，庚绝在寅，辛绝在卯，壬绝在巳，癸绝在午
        jue_wei_mapping = {
            0: 8,   # 甲绝在申
            1: 9,   # 乙绝在酉
            2: 11,  # 丙绝在亥
            3: 0,   # 丁绝在子
            4: 11,  # 戊绝在亥
            5: 0,   # 己绝在子
            6: 2,   # 庚绝在寅
            7: 3,   # 辛绝在卯
            8: 5,   # 壬绝在巳
            9: 6    # 癸绝在午
        }
        
        jue_wei = jue_wei_mapping.get(day_stem_index)
        
        # 如果日支是日干的绝位，则可能触发绝处逢生
        if jue_wei == day_branch_index:
            # 简化判断：当日干在月将或时支有生助时返回True
            # 实际应用中需要更复杂的生克计算
            return True
        
        return False
    
    @staticmethod
    def _check_chong_po(day_branch_index: int) -> bool:
        """
        判断是否冲破（简化版）
        
        Args:
            day_branch_index: 日支索引
            
        Returns:
            bool: 是否冲破
        """
        # 冲破关系：子午冲，丑未冲，寅申冲，卯酉冲，辰戌冲，巳亥冲
        chong_po_pairs = [(0, 6), (1, 7), (2, 8), (3, 9), (4, 10), (5, 11)]
        
        # 检查日支是否在冲对关系中
        for pair in chong_po_pairs:
            if day_branch_index in pair:
                return True
        
        return False