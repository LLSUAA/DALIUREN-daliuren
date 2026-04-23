from typing import List, Optional
from pydantic import BaseModel, Field, validator
from engine.components.base_comp import OrbitComp
from engine.core.constants import STEM_PARASITIC_MAPPING


class LessonNode(BaseModel):
    """
    四课节点数据类
    表示大六壬推演中的一课结构
    """
    lesson_id: int = Field(..., ge=1, le=4, description="课序编号，范围1-4")
    bottom_earth_index: int = Field(..., ge=0, le=11, description="底层地盘索引")
    top_heaven_index: int = Field(..., ge=0, le=11, description="顶层天盘索引")

    @validator('lesson_id')
    def validate_lesson_id(cls, v):
        if not 1 <= v <= 4:
            raise ValueError(f"课序编号必须在1-4范围内，当前值: {v}")
        return v

    @validator('bottom_earth_index', 'top_heaven_index')
    def validate_index_range(cls, v):
        if not 0 <= v <= 11:
            raise ValueError(f"索引值必须在0-11范围内，当前值: {v}")
        return v

    @property
    def is_valid(self) -> bool:
        """检查节点是否有效"""
        return 1 <= self.lesson_id <= 4 and 0 <= self.bottom_earth_index <= 11 and 0 <= self.top_heaven_index <= 11


class FourLessonsSystem:
    """
    四课提取系统 - 无状态纯计算类
    负责从天地盘矩阵中提取四课结构
    """

    @staticmethod
    def extract_lessons(
        orbit_matrix: List[OrbitComp], 
        day_stem_index: int, 
        day_branch_index: int
    ) -> List[LessonNode]:
        """
        从天地盘矩阵中提取四课结构
        
        Args:
            orbit_matrix: 天地盘轨道矩阵
            day_stem_index: 日干索引，范围0-9
            day_branch_index: 日支索引，范围0-11
            
        Returns:
            List[LessonNode]: 包含4个LessonNode的列表，按课序排列
            
        Raises:
            ValueError: 当输入参数无效时抛出异常
        """
        # 参数验证
        if not 0 <= day_stem_index <= 9:
            raise ValueError(f"日干索引必须在0-9范围内，当前值: {day_stem_index}")
        if not 0 <= day_branch_index <= 11:
            raise ValueError(f"日支索引必须在0-11范围内，当前值: {day_branch_index}")
        
        # 验证轨道矩阵
        if len(orbit_matrix) != 12:
            raise ValueError(f"轨道矩阵必须包含12个组件，当前数量: {len(orbit_matrix)}")
        
        lessons: List[LessonNode] = []
        
        # 第一课：客户端核心
        first_lesson = FourLessonsSystem._extract_first_lesson(orbit_matrix, day_stem_index)
        lessons.append(first_lesson)
        
        # 第二课：客户端状态
        second_lesson = FourLessonsSystem._extract_second_lesson(orbit_matrix, first_lesson.top_heaven_index)
        lessons.append(second_lesson)
        
        # 第三课：目标核心
        third_lesson = FourLessonsSystem._extract_third_lesson(orbit_matrix, day_branch_index)
        lessons.append(third_lesson)
        
        # 第四课：目标状态
        fourth_lesson = FourLessonsSystem._extract_fourth_lesson(orbit_matrix, third_lesson.top_heaven_index)
        lessons.append(fourth_lesson)
        
        return lessons

    @staticmethod
    def _extract_first_lesson(orbit_matrix: List[OrbitComp], day_stem_index: int) -> LessonNode:
        """提取第一课：客户端核心"""
        # 获取天干寄宫映射
        parasitic_earth_index = STEM_PARASITIC_MAPPING[day_stem_index]
        
        # 在轨道矩阵中寻找对应的组件
        orbit_comp = FourLessonsSystem._find_orbit_by_earth_index(orbit_matrix, parasitic_earth_index)
        
        return LessonNode(
            lesson_id=1,
            bottom_earth_index=parasitic_earth_index,
            top_heaven_index=orbit_comp.heaven_index
        )

    @staticmethod
    def _extract_second_lesson(orbit_matrix: List[OrbitComp], first_lesson_top: int) -> LessonNode:
        """提取第二课：客户端状态"""
        # 在轨道矩阵中寻找earth_index等于第一课top_heaven_index的组件
        orbit_comp = FourLessonsSystem._find_orbit_by_earth_index(orbit_matrix, first_lesson_top)
        
        return LessonNode(
            lesson_id=2,
            bottom_earth_index=first_lesson_top,
            top_heaven_index=orbit_comp.heaven_index
        )

    @staticmethod
    def _extract_third_lesson(orbit_matrix: List[OrbitComp], day_branch_index: int) -> LessonNode:
        """提取第三课：目标核心"""
        # 在轨道矩阵中寻找earth_index等于day_branch_index的组件
        orbit_comp = FourLessonsSystem._find_orbit_by_earth_index(orbit_matrix, day_branch_index)
        
        return LessonNode(
            lesson_id=3,
            bottom_earth_index=day_branch_index,
            top_heaven_index=orbit_comp.heaven_index
        )

    @staticmethod
    def _extract_fourth_lesson(orbit_matrix: List[OrbitComp], third_lesson_top: int) -> LessonNode:
        """提取第四课：目标状态"""
        # 在轨道矩阵中寻找earth_index等于第三课top_heaven_index的组件
        orbit_comp = FourLessonsSystem._find_orbit_by_earth_index(orbit_matrix, third_lesson_top)
        
        return LessonNode(
            lesson_id=4,
            bottom_earth_index=third_lesson_top,
            top_heaven_index=orbit_comp.heaven_index
        )

    @staticmethod
    def _find_orbit_by_earth_index(orbit_matrix: List[OrbitComp], earth_index: int) -> OrbitComp:
        """根据地盘索引在轨道矩阵中查找对应的组件"""
        for orbit_comp in orbit_matrix:
            if orbit_comp.earth_index == earth_index:
                return orbit_comp
        
        raise ValueError(f"未找到对应的地盘索引: {earth_index}")

    @staticmethod
    def validate_lessons_structure(lessons: List[LessonNode]) -> bool:
        """验证四课结构的完整性"""
        if len(lessons) != 4:
            return False
        
        # 检查课序编号是否正确
        lesson_ids = [lesson.lesson_id for lesson in lessons]
        if lesson_ids != [1, 2, 3, 4]:
            return False
        
        # 检查所有节点是否有效
        for lesson in lessons:
            if not lesson.is_valid:
                return False
        
        return True

    @staticmethod
    def get_lesson_by_id(lessons: List[LessonNode], lesson_id: int) -> Optional[LessonNode]:
        """根据课序编号获取对应的课节点"""
        for lesson in lessons:
            if lesson.lesson_id == lesson_id:
                return lesson
        return None