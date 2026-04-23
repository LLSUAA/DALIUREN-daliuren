from typing import Dict, List, Any
from engine.systems.astrolabe_sys import AstrolabeSystem
from engine.systems.four_lessons_sys import FourLessonsSystem, LessonNode
from engine.systems.routing_sys import RoutingGatewaySystem, RouteResult
from engine.components.base_comp import OrbitComp


class DaLiuRenEngine:
    """
    大六壬物理引擎 - 对外API接口类
    提供完整的推演流水线
    """

    @staticmethod
    def generate_snapshot(
        zhan_shi_index: int, 
        yue_jiang_index: int, 
        day_stem_index: int, 
        day_branch_index: int
    ) -> Dict[str, Any]:
        """
        生成大六壬推演快照
        
        Args:
            zhan_shi_index: 占时索引，范围0-11
            yue_jiang_index: 月将索引，范围0-11
            day_stem_index: 日干索引，范围0-9
            day_branch_index: 日支索引，范围0-11
            
        Returns:
            Dict[str, Any]: 推演快照结果
            
        Raises:
            ValueError: 当输入参数无效时抛出异常
        """
        # 参数验证
        if not 0 <= zhan_shi_index <= 11:
            raise ValueError(f"占时索引必须在0-11范围内，当前值: {zhan_shi_index}")
        if not 0 <= yue_jiang_index <= 11:
            raise ValueError(f"月将索引必须在0-11范围内，当前值: {yue_jiang_index}")
        if not 0 <= day_stem_index <= 9:
            raise ValueError(f"日干索引必须在0-9范围内，当前值: {day_stem_index}")
        if not 0 <= day_branch_index <= 11:
            raise ValueError(f"日支索引必须在0-11范围内，当前值: {day_branch_index}")
        
        # Step 1: 调用 AstrolabeSystem.calculate_orbit_matrix 生成宇宙空间矩阵
        orbit_matrix = AstrolabeSystem.calculate_orbit_matrix(zhan_shi_index, yue_jiang_index)
        
        # Step 2: 调用 FourLessonsSystem.extract_lessons 提取四课
        lessons = FourLessonsSystem.extract_lessons(orbit_matrix, day_stem_index, day_branch_index)
        
        # Step 3: 调用 RoutingGatewaySystem.dispatch_route 进行网关路由判定
        route_result = RoutingGatewaySystem.dispatch_route(lessons, day_stem_index)
        
        # Step 4: 组装 AST (纯净的 JSON/Dict 格式)
        snapshot = DaLiuRenEngine._assemble_snapshot(
            zhan_shi_index, yue_jiang_index, day_stem_index, day_branch_index,
            orbit_matrix, lessons, route_result
        )
        
        return snapshot

    @staticmethod
    def _assemble_snapshot(
        zhan_shi_index: int,
        yue_jiang_index: int,
        day_stem_index: int,
        day_branch_index: int,
        orbit_matrix: List[OrbitComp],
        lessons: List[LessonNode],
        route_result: RouteResult
    ) -> Dict[str, Any]:
        """
        组装推演快照
        
        Args:
            zhan_shi_index: 占时索引
            yue_jiang_index: 月将索引
            day_stem_index: 日干索引
            day_branch_index: 日支索引
            orbit_matrix: 轨道矩阵
            lessons: 四课列表
            route_result: 路由结果
            
        Returns:
            Dict[str, Any]: 组装后的快照
        """
        # 组装参数部分
        params = {
            "zhan_shi": zhan_shi_index,
            "yue_jiang": yue_jiang_index,
            "day_stem": day_stem_index,
            "day_branch": day_branch_index
        }
        
        # 组装轨道矩阵部分（简化版，只包含index）
        orbit_matrix_simplified = []
        for orbit_comp in orbit_matrix:
            orbit_info = {
                "earth": orbit_comp.earth_index,
                "heaven": orbit_comp.heaven_index
            }
            orbit_matrix_simplified.append(orbit_info)
        
        # 组装四课部分
        four_lessons_simplified = []
        for lesson in lessons:
            lesson_info = {
                "id": lesson.lesson_id,
                "bottom": lesson.bottom_earth_index,
                "top": lesson.top_heaven_index
            }
            four_lessons_simplified.append(lesson_info)
        
        # 组装路由决策部分
        route_decision = {
            "method": route_result.route_method.value,
            "init_node_lesson_id": route_result.init_node_lesson_id,
            "is_bottom_up": route_result.is_bottom_up
        }
        
        # 组装完整快照
        snapshot = {
            "params": params,
            "orbit_matrix": orbit_matrix_simplified,
            "four_lessons": four_lessons_simplified,
            "route_decision": route_decision
        }
        
        return snapshot

    @staticmethod
    def validate_snapshot(snapshot: Dict[str, Any]) -> bool:
        """
        验证快照结构的完整性
        
        Args:
            snapshot: 推演快照
            
        Returns:
            bool: 快照是否完整有效
        """
        required_keys = {"params", "orbit_matrix", "four_lessons", "route_decision"}
        if not required_keys.issubset(snapshot.keys()):
            return False
        
        # 验证参数部分
        params = snapshot["params"]
        required_params = {"zhan_shi", "yue_jiang", "day_stem", "day_branch"}
        if not required_params.issubset(params.keys()):
            return False
        
        # 验证轨道矩阵部分
        orbit_matrix = snapshot["orbit_matrix"]
        if len(orbit_matrix) != 12:
            return False
        
        # 验证四课部分
        four_lessons = snapshot["four_lessons"]
        if len(four_lessons) != 4:
            return False
        
        # 验证路由决策部分
        route_decision = snapshot["route_decision"]
        required_route_keys = {"method", "init_node_lesson_id", "is_bottom_up"}
        if not required_route_keys.issubset(route_decision.keys()):
            return False
        
        return True

    @staticmethod
    def get_snapshot_summary(snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取快照摘要信息
        
        Args:
            snapshot: 推演快照
            
        Returns:
            Dict[str, Any]: 摘要信息
        """
        params = snapshot["params"]
        route_decision = snapshot["route_decision"]
        
        summary = {
            "zhan_shi": params["zhan_shi"],
            "yue_jiang": params["yue_jiang"],
            "day_stem": params["day_stem"],
            "day_branch": params["day_branch"],
            "route_method": route_decision["method"],
            "init_lesson": route_decision["init_node_lesson_id"],
            "is_bottom_up": route_decision["is_bottom_up"]
        }
        
        return summary