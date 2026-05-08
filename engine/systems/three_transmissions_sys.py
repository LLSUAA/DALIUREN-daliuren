"""
大六壬三传推演系统
基于四课和路由决策，推导初传、中传、末传

核心逻辑：
- 初传 (Chu Chuan)：基于路由给出的 init_node_lesson_id，取该课的 top_heaven_index
- 中传 (Zhong Chuan)：将初传的地支当做地盘，去 orbit_matrix 中寻找它头顶的 heaven_index
- 末传 (Mo Chuan)：将中传的地支当做地盘，再去 orbit_matrix 中寻找它头顶的 heaven_index
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from engine.components.base_comp import OrbitComp
from engine.systems.four_lessons_sys import LessonNode
from engine.core.schemas import BRANCHES


class TransmissionNode(BaseModel):
    """
    三传节点数据模型
    
    Attributes:
        order: 传序 (1=初传, 2=中传, 3=末传)
        name: 名称 ("初传"/"中传"/"末传")
        heaven_index: 天盘地支索引 (0-11)，代表所临天盘宫位
        earth_index: 地盘地支索引 (0-11)，代表此传立足的地盘宫位
        branch_name: 地支汉字名称
    """
    order: int = Field(..., ge=1, le=3, description="传序: 1=初传, 2=中传, 3=末传")
    name: str = Field(..., description="名称: 初传/中传/末传")
    heaven_index: int = Field(..., ge=0, le=11, description="天盘地支索引 (此传临于天盘何宫)")
    earth_index: int = Field(..., ge=0, le=11, description="地盘地支索引 (此传立足地盘何宫)")
    branch_name: str = Field(..., description="地支名称，如'子'、'丑'")

    @validator('order')
    def validate_order(cls, v):
        if v not in (1, 2, 3):
            raise ValueError(f"传序必须为 1/2/3，当前值: {v}")
        return v


class ThreeTransmissionsSystem:
    """
    三传推演系统 —— 无状态纯计算类
    
    根据四课和路由决策结果，推导大六壬的初传、中传、末传三传链。
    三传是占断吉凶的核心推演链，代表事件从发端→发展→结局的因果过程。
    """

    @staticmethod
    def generate_transmissions(
        orbit_matrix: List[OrbitComp],
        four_lessons: List[LessonNode],
        route_decision: Any  # RouteResult 对象或 dict
    ) -> List[TransmissionNode]:
        """
        生成三传推演结果
        
        Args:
            orbit_matrix: 天地盘轨道矩阵 (12个 OrbitComp)
            four_lessons: 四课节点列表 (4个 LessonNode)
            route_decision: 路由决策结果 (RouteResult 对象或包含 init_node_lesson_id 的字典)
            
        Returns:
            List[TransmissionNode]: 包含初传、中传、末传的列表
            
        Raises:
            ValueError: 当路由决策或四课数据无效时
        """
        # ── 兼容 RouteResult 对象和 dict 两种格式 ──
        if hasattr(route_decision, 'init_node_lesson_id'):
            init_lesson_id = route_decision.init_node_lesson_id
        elif isinstance(route_decision, dict):
            init_lesson_id = route_decision.get("init_node_lesson_id")
            if init_lesson_id is None:
                raise ValueError("route_decision 字典中缺少 init_node_lesson_id")
        else:
            raise TypeError(f"route_decision 类型无效: {type(route_decision)}")

        # ── Step 1: 初传 —— 取触发课的 top_heaven_index ──
        init_lesson = ThreeTransmissionsSystem._find_lesson_by_id(four_lessons, init_lesson_id)
        if init_lesson is None:
            raise ValueError(f"四课中未找到课序编号: {init_lesson_id}")

        chu_heaven = init_lesson.top_heaven_index
        chu_earth = init_lesson.bottom_earth_index

        # ── Step 2: 中传 —— 初传的地支当做地盘，找其头顶的天盘 ──
        zhong_heaven = ThreeTransmissionsSystem._resolve_heaven(orbit_matrix, chu_heaven)
        zhong_earth = chu_heaven

        # ── Step 3: 末传 —— 中传的地支当做地盘，找其头顶的天盘 ──
        mo_heaven = ThreeTransmissionsSystem._resolve_heaven(orbit_matrix, zhong_heaven)
        mo_earth = zhong_heaven

        return [
            TransmissionNode(
                order=1,
                name="初传",
                heaven_index=chu_heaven,
                earth_index=chu_earth,
                branch_name=BRANCHES[chu_heaven]
            ),
            TransmissionNode(
                order=2,
                name="中传",
                heaven_index=zhong_heaven,
                earth_index=zhong_earth,
                branch_name=BRANCHES[zhong_heaven]
            ),
            TransmissionNode(
                order=3,
                name="末传",
                heaven_index=mo_heaven,
                earth_index=mo_earth,
                branch_name=BRANCHES[mo_heaven]
            ),
        ]

    @staticmethod
    def _find_lesson_by_id(
        four_lessons: List[LessonNode], lesson_id: int
    ) -> Optional[LessonNode]:
        """根据课序编号查找四课中的节点"""
        for lesson in four_lessons:
            if lesson.lesson_id == lesson_id:
                return lesson
        return None

    @staticmethod
    def _resolve_heaven(orbit_matrix: List[OrbitComp], earth_index: int) -> int:
        """
        在天地盘矩阵中，根据地盘索引解析对应的天盘索引
        
        Args:
            orbit_matrix: 天地盘矩阵
            earth_index: 地盘索引
            
        Returns:
            int: 对应的天盘索引
        """
        for comp in orbit_matrix:
            if comp.earth_index == earth_index:
                return comp.heaven_index
        raise ValueError(f"orbit_matrix 中未找到 earth_index={earth_index} 的轨道组件")
