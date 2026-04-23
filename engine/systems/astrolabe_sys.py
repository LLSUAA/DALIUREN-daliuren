from typing import List
from engine.components.base_comp import OrbitComp
from engine.core.constants import EarthlyBranch


class AstrolabeSystem:
    """
    宇宙空间生成系统 - 无状态纯计算类
    负责计算天地盘矩阵映射关系
    """

    @staticmethod
    def calculate_orbit_matrix(zhan_shi_index: int, yue_jiang_index: int) -> List[OrbitComp]:
        """
        计算完整的天地盘轨道矩阵
        
        Args:
            zhan_shi_index: 占时索引（地盘参数），范围0-11
            yue_jiang_index: 月将索引（天盘参数），范围0-11
            
        Returns:
            List[OrbitComp]: 包含12个OrbitComp的列表，形成完整的空间快照
            
        Raises:
            ValueError: 当输入参数超出有效范围时抛出异常
        """
        # 参数验证
        if not 0 <= zhan_shi_index <= 11:
            raise ValueError(f"占时索引必须在0-11范围内，当前值: {zhan_shi_index}")
        if not 0 <= yue_jiang_index <= 11:
            raise ValueError(f"月将索引必须在0-11范围内，当前值: {yue_jiang_index}")
        
        # 计算步长偏移量
        offset = (yue_jiang_index - zhan_shi_index) % 12
        
        # 生成轨道矩阵
        orbit_matrix: List[OrbitComp] = []
        
        for earth_index in range(12):
            # 计算对应的天盘索引
            heaven_index = (earth_index + offset) % 12
            
            # 创建轨道组件实例
            orbit_comp = OrbitComp(
                earth_index=earth_index,
                heaven_index=heaven_index
            )
            
            orbit_matrix.append(orbit_comp)
        
        return orbit_matrix

    @staticmethod
    def get_alignment_positions(orbit_matrix: List[OrbitComp]) -> List[int]:
        """
        获取天地盘对齐的位置索引列表
        
        Args:
            orbit_matrix: 轨道矩阵列表
            
        Returns:
            List[int]: 对齐位置的地盘索引列表
        """
        alignment_positions = []
        
        for orbit_comp in orbit_matrix:
            if orbit_comp.is_aligned:
                alignment_positions.append(orbit_comp.earth_index)
        
        return alignment_positions

    @staticmethod
    def get_heaven_position_by_earth(orbit_matrix: List[OrbitComp], earth_index: int) -> int:
        """
        根据地盘索引获取对应的天盘索引
        
        Args:
            orbit_matrix: 轨道矩阵列表
            earth_index: 地盘索引，范围0-11
            
        Returns:
            int: 对应的天盘索引
            
        Raises:
            ValueError: 当地盘索引无效时抛出异常
        """
        if not 0 <= earth_index <= 11:
            raise ValueError(f"地盘索引必须在0-11范围内，当前值: {earth_index}")
        
        for orbit_comp in orbit_matrix:
            if orbit_comp.earth_index == earth_index:
                return orbit_comp.heaven_index
        
        # 理论上不会执行到这里，因为矩阵包含所有0-11的地盘索引
        raise ValueError(f"未找到对应的地盘索引: {earth_index}")

    @staticmethod
    def get_earth_position_by_heaven(orbit_matrix: List[OrbitComp], heaven_index: int) -> int:
        """
        根据天盘索引获取对应的地盘索引
        
        Args:
            orbit_matrix: 轨道矩阵列表
            heaven_index: 天盘索引，范围0-11
            
        Returns:
            int: 对应的地盘索引
            
        Raises:
            ValueError: 当天盘索引无效时抛出异常
        """
        if not 0 <= heaven_index <= 11:
            raise ValueError(f"天盘索引必须在0-11范围内，当前值: {heaven_index}")
        
        for orbit_comp in orbit_matrix:
            if orbit_comp.heaven_index == heaven_index:
                return orbit_comp.earth_index
        
        # 理论上不会执行到这里，因为矩阵包含所有0-11的天盘索引
        raise ValueError(f"未找到对应的天盘索引: {heaven_index}")

    @staticmethod
    def validate_orbit_matrix(orbit_matrix: List[OrbitComp]) -> bool:
        """
        验证轨道矩阵的完整性
        
        Args:
            orbit_matrix: 轨道矩阵列表
            
        Returns:
            bool: 矩阵是否完整有效
        """
        if len(orbit_matrix) != 12:
            return False
        
        # 检查是否包含所有地盘索引
        earth_indices = set(orbit.earth_index for orbit in orbit_matrix)
        if earth_indices != set(range(12)):
            return False
        
        # 检查是否包含所有天盘索引
        heaven_indices = set(orbit.heaven_index for orbit in orbit_matrix)
        if heaven_indices != set(range(12)):
            return False
        
        return True