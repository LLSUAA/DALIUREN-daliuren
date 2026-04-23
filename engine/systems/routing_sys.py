from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator
from engine.systems.four_lessons_sys import LessonNode
from engine.core.constants import RoutingMethod, WuXing, YinYang, BRANCH_WUXING_MAPPING, BRANCH_YINYANG_MAPPING, STEM_YINYANG_MAPPING, is_clashing


class RouteResult(BaseModel):
    """
    路由结果数据类
    表示九宗门路由网关的决策结果
    """
    route_method: RoutingMethod = Field(..., description="路由方法枚举")
    init_node_lesson_id: int = Field(..., ge=1, le=4, description="触发初传的课序编号，范围1-4")
    is_bottom_up: bool = Field(..., description="是否为下克上/贼")

    @validator('init_node_lesson_id')
    def validate_lesson_id(cls, v):
        if not 1 <= v <= 4:
            raise ValueError(f"课序编号必须在1-4范围内，当前值: {v}")
        return v


class RoutingGatewaySystem:
    """
    九宗门 API 路由网关系统 - 无状态类
    负责五行生克伤害结算和路由决策
    """

    @staticmethod
    def scan_clashes(lessons: List[LessonNode]) -> List[Dict]:
        """
        扫描四课中的五行冲突情况
        
        Args:
            lessons: 四课节点列表
            
        Returns:
            List[Dict]: 包含冲突详情的列表
            
        Raises:
            ValueError: 当四课结构无效时抛出异常
        """
        if len(lessons) != 4:
            raise ValueError(f"四课结构必须包含4个节点，当前数量: {len(lessons)}")
        
        clashes = []
        
        for lesson in lessons:
            # 获取地盘五行和天盘五行
            bottom_wuxing = BRANCH_WUXING_MAPPING.get(lesson.bottom_earth_index)
            top_wuxing = BRANCH_WUXING_MAPPING.get(lesson.top_heaven_index)
            
            if bottom_wuxing is None or top_wuxing is None:
                raise ValueError(f"无效的地盘或天盘索引: {lesson.bottom_earth_index}, {lesson.top_heaven_index}")
            
            # 检查下克上（贼）：地盘克天盘
            is_bottom_clashing_top = is_clashing(bottom_wuxing, top_wuxing)
            
            # 检查上克下（克）：天盘克地盘
            is_top_clashing_bottom = is_clashing(top_wuxing, bottom_wuxing)
            
            if is_bottom_clashing_top or is_top_clashing_bottom:
                clash_info = {
                    'lesson_id': lesson.lesson_id,
                    'bottom_earth_index': lesson.bottom_earth_index,
                    'top_heaven_index': lesson.top_heaven_index,
                    'bottom_wuxing': bottom_wuxing,
                    'top_wuxing': top_wuxing,
                    'is_bottom_clashing_top': is_bottom_clashing_top,
                    'is_top_clashing_bottom': is_top_clashing_bottom
                }
                clashes.append(clash_info)
        
        return clashes

    @staticmethod
    def dispatch_route(lessons: List[LessonNode], day_stem_index: int) -> RouteResult:
        """
        路由入口：根据四课冲突情况决定路由方法
        
        Args:
            lessons: 四课节点列表
            day_stem_index: 日干索引，范围0-9
            
        Returns:
            RouteResult: 路由决策结果
            
        Raises:
            ValueError: 当日干索引无效时抛出异常
        """
        # 参数验证
        if not 0 <= day_stem_index <= 9:
            raise ValueError(f"日干索引必须在0-9范围内，当前值: {day_stem_index}")
        
        # 验证四课结构
        if len(lessons) != 4:
            raise ValueError(f"四课结构必须包含4个节点，当前数量: {len(lessons)}")
        
        # 扫描冲突情况
        clashes = RoutingGatewaySystem.scan_clashes(lessons)
        
        # 获取日干极性
        day_stem_yinyang = STEM_YINYANG_MAPPING[day_stem_index]
        
        # 阶段一逻辑：贼克法拦截
        
        # 筛选下克上（贼）冲突
        bottom_clashes = [clash for clash in clashes if clash['is_bottom_clashing_top']]
        
        # 筛选上克下（克）冲突
        top_clashes = [clash for clash in clashes if clash['is_top_clashing_bottom']]
        
        # 情况1：只有1个下克上（贼）
        if len(bottom_clashes) == 1 and len(top_clashes) == 0:
            clash_info = bottom_clashes[0]
            return RouteResult(
                route_method=RoutingMethod.ZEI_KE,
                init_node_lesson_id=clash_info['lesson_id'],
                is_bottom_up=True
            )
        
        # 情况2：没有下克上，但只有1个上克下（克）
        if len(bottom_clashes) == 0 and len(top_clashes) == 1:
            clash_info = top_clashes[0]
            return RouteResult(
                route_method=RoutingMethod.ZEI_KE,
                init_node_lesson_id=clash_info['lesson_id'],
                is_bottom_up=False
            )
        
        # 阶段二逻辑：比用法过滤
        
        # 情况3：多个下克上（贼）
        if len(bottom_clashes) > 1:
            # 比对极性，筛选与日干极性相同的冲突课
            matching_clashes = []
            for clash in bottom_clashes:
                branch_yinyang = BRANCH_YINYANG_MAPPING[clash['top_heaven_index']]
                if branch_yinyang == day_stem_yinyang:
                    matching_clashes.append(clash)
            
            # 如果只有1课极性相同，命中比用法
            if len(matching_clashes) == 1:
                clash_info = matching_clashes[0]
                return RouteResult(
                    route_method=RoutingMethod.BI_YONG,
                    init_node_lesson_id=clash_info['lesson_id'],
                    is_bottom_up=True
                )
        
        # 情况4：多个上克下（克）且无贼
        if len(top_clashes) > 1 and len(bottom_clashes) == 0:
            # 比对极性，筛选与日干极性相同的冲突课
            matching_clashes = []
            for clash in top_clashes:
                branch_yinyang = BRANCH_YINYANG_MAPPING[clash['top_heaven_index']]
                if branch_yinyang == day_stem_yinyang:
                    matching_clashes.append(clash)
            
            # 如果只有1课极性相同，命中比用法
            if len(matching_clashes) == 1:
                clash_info = matching_clashes[0]
                return RouteResult(
                    route_method=RoutingMethod.BI_YONG,
                    init_node_lesson_id=clash_info['lesson_id'],
                    is_bottom_up=False
                )
        
        # 阶段三逻辑：涉害法兜底（MVP简化版）
        
        # 情况5：经过比用法过滤后仍有冲突或平局
        # 合并所有冲突课（包括下克上和上克下）
        all_clashes = bottom_clashes + top_clashes
        
        if len(all_clashes) > 0:
            # 降级策略：选取lesson_id最小的冲突课
            selected_clash = min(all_clashes, key=lambda x: x['lesson_id'])
            
            # 判断克战方向
            is_bottom_up = selected_clash['is_bottom_clashing_top']
            
            return RouteResult(
                route_method=RoutingMethod.SHE_HAI,
                init_node_lesson_id=selected_clash['lesson_id'],
                is_bottom_up=is_bottom_up
            )
        
        # 情况6：无克情况 - 安全降级协议
        if len(all_clashes) == 0:
            # 阶段四逻辑：遥克法降级
            yao_ke_result = RoutingGatewaySystem._try_yao_ke_method(lessons, day_stem_index)
            if yao_ke_result:
                return yao_ke_result
            
            # 阶段五逻辑：昴星法/别责法兜底
            return RoutingGatewaySystem._fallback_mao_xing_method(lessons)
        
        # 理论上不会执行到这里
        raise RuntimeError("未知的路由决策情况")

    @staticmethod
    def get_clash_summary(clashes: List[Dict]) -> Dict[str, int]:
        """
        获取冲突统计摘要
        
        Args:
            clashes: 冲突详情列表
            
        Returns:
            Dict[str, int]: 冲突统计信息
        """
        bottom_clash_count = sum(1 for clash in clashes if clash['is_bottom_clashing_top'])
        top_clash_count = sum(1 for clash in clashes if clash['is_top_clashing_bottom'])
        
        return {
            'total_clashes': len(clashes),
            'bottom_clashes': bottom_clash_count,
            'top_clashes': top_clash_count
        }

    @staticmethod
    def validate_route_result(route_result: RouteResult) -> bool:
        """
        验证路由结果的合理性
        
        Args:
            route_result: 路由结果
            
        Returns:
            bool: 结果是否合理
        """
        if not 1 <= route_result.init_node_lesson_id <= 4:
            return False
        
        if route_result.route_method not in RoutingMethod:
            return False
        
        return True

    @staticmethod
    def _try_yao_ke_method(lessons: List[LessonNode], day_stem_index: int) -> Optional[RouteResult]:
        """
        尝试遥克法降级逻辑
        
        Args:
            lessons: 四课节点列表
            day_stem_index: 日干索引
            
        Returns:
            Optional[RouteResult]: 遥克法结果，如果不满足条件则返回None
        """
        from engine.core.constants import STEM_WUXING_MAPPING, BRANCH_WUXING_MAPPING, is_clashing
        
        # 获取日干五行
        day_stem_wuxing = STEM_WUXING_MAPPING.get(day_stem_index)
        if day_stem_wuxing is None:
            return None
        
        # 寻找与日干相克的课（遥克法：日干克天盘或天盘克日干）
        yao_ke_lessons = []
        
        for lesson in lessons:
            # 获取天盘五行
            heaven_wuxing = BRANCH_WUXING_MAPPING.get(lesson.top_heaven_index)
            if heaven_wuxing is None:
                continue
            
            # 检查日干克天盘（日干克遥）
            is_day_clashing_heaven = is_clashing(day_stem_wuxing, heaven_wuxing)
            # 检查天盘克日干（遥克日干）
            is_heaven_clashing_day = is_clashing(heaven_wuxing, day_stem_wuxing)
            
            if is_day_clashing_heaven or is_heaven_clashing_day:
                yao_ke_lessons.append({
                    'lesson': lesson,
                    'is_day_clashing_heaven': is_day_clashing_heaven,
                    'is_heaven_clashing_day': is_heaven_clashing_day
                })
        
        # 如果找到遥克课，优先选择日干克天盘的课
        if yao_ke_lessons:
            # 优先选择日干克天盘的课
            day_clash_lessons = [item for item in yao_ke_lessons if item['is_day_clashing_heaven']]
            if day_clash_lessons:
                selected_lesson = min(day_clash_lessons, key=lambda x: x['lesson'].lesson_id)
                return RouteResult(
                    route_method=RoutingMethod.YAO_KE,
                    init_node_lesson_id=selected_lesson['lesson'].lesson_id,
                    is_bottom_up=False
                )
            
            # 如果没有日干克天盘的课，选择天盘克日干的课
            heaven_clash_lessons = [item for item in yao_ke_lessons if item['is_heaven_clashing_day']]
            if heaven_clash_lessons:
                selected_lesson = min(heaven_clash_lessons, key=lambda x: x['lesson'].lesson_id)
                return RouteResult(
                    route_method=RoutingMethod.YAO_KE,
                    init_node_lesson_id=selected_lesson['lesson'].lesson_id,
                    is_bottom_up=False
                )
        
        return None

    @staticmethod
    def _fallback_mao_xing_method(lessons: List[LessonNode]) -> RouteResult:
        """
        昴星法/别责法兜底逻辑
        
        Args:
            lessons: 四课节点列表
            
        Returns:
            RouteResult: 兜底路由结果
        """
        # 兜底策略：根据四课结构选择最合适的发用课
        # 简化实现：优先选择第1课，如果存在特殊结构则调整
        
        # 检查是否存在特殊结构（如伏吟、反吟等）
        has_special_structure = RoutingGatewaySystem._check_special_structure(lessons)
        
        if has_special_structure:
            # 如果有特殊结构，尝试选择更合适的课
            # 简化实现：选择课序最小的课
            selected_lesson_id = 1
        else:
            # 标准昴星法：阳日取地盘酉上神，阴日取天盘酉下神
            # 简化实现：选择第1课作为发用
            selected_lesson_id = 1
        
        # 确保lesson_id在有效范围内
        selected_lesson_id = max(1, min(4, selected_lesson_id))
        
        return RouteResult(
            route_method=RoutingMethod.MAO_XING,
            init_node_lesson_id=selected_lesson_id,
            is_bottom_up=False
        )

    @staticmethod
    def _check_special_structure(lessons: List[LessonNode]) -> bool:
        """
        检查是否存在特殊结构（伏吟、反吟等）
        
        Args:
            lessons: 四课节点列表
            
        Returns:
            bool: 是否存在特殊结构
        """
        # 简化实现：检查是否有天地盘相同的情况（伏吟）
        for lesson in lessons:
            if lesson.bottom_earth_index == lesson.top_heaven_index:
                return True
        
        # 检查是否有反吟结构（地盘与天盘相差6位）
        for lesson in lessons:
            diff = abs(lesson.bottom_earth_index - lesson.top_heaven_index)
            if diff == 6 or diff == 6 % 12:
                return True
        
        return False