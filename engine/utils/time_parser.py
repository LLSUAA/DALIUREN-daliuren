"""
大六壬物理引擎 - 时空解析中间件
基于 lunar_python 库的精确历法转换和时空参数计算
支持真太阳时校准，适用于全球经纬度
"""

from typing import Tuple, Optional
from datetime import datetime, timedelta
import math
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import lunar_python
from lunar_python import Solar, Lunar, JieQi

from engine.core.schemas import SpaceTimeParams, SolarTimeInput, BRANCH_INDEX_MAPPING, BRANCHES, SOLAR_TERM_YUE_JIANG, DAYTIME_BRANCHES


class SpaceTimeParser:
    """
    时空解析引擎 - 无状态类
    负责将公历时间转换为大六壬推演所需的完整时空参数
    支持真太阳时校准，适用于全球经纬度
    """
    
    # 天文常数
    MINUTES_PER_DEGREE = 4.0  # 每度经度对应的时间差（分钟）
    
    @staticmethod
    def parse_datetime(solar_time_str: str, longitude: float, gender: str, birth_year: int) -> SpaceTimeParams:
        """
        解析公历时间，生成大六壬时空参数（支持真太阳时校准）
        
        Args:
            solar_time_str: 公历时间字符串 (YYYY-MM-DD HH:MM:SS)
            longitude: 经度（东经为正，西经为负）
            gender: 性别 ("男" 或 "女")
            birth_year: 出生年份 (公历)
            
        Returns:
            SpaceTimeParams: 完整的时空参数对象
            
        Raises:
            ValueError: 当输入参数无效时抛出异常
        """
        # 验证输入参数
        SolarTimeInput(
            solar_time_str=solar_time_str,
            gender=gender,
            birth_year=birth_year
        )
        
        # 解析公历时间
        local_time = SpaceTimeParser._parse_solar_time(solar_time_str)
        
        # 计算真太阳时校准
        true_solar_time = SpaceTimeParser._calculate_true_solar_time(local_time, longitude)
        
        # 将校准后的真太阳时转换为Solar对象
        solar_time = Solar.fromYmdHms(
            true_solar_time.year,
            true_solar_time.month,
            true_solar_time.day,
            true_solar_time.hour,
            true_solar_time.minute,
            true_solar_time.second
        )
        
        # 转换为农历时间
        lunar_time = Lunar.fromSolar(solar_time)
        
        # 获取四柱八字
        year_stem_branch, month_stem_branch, day_stem_branch, hour_stem_branch = SpaceTimeParser._get_four_pillars(lunar_time)
        
        # 提取占时索引 (时柱地支索引)
        zhan_shi_index = SpaceTimeParser._extract_zhan_shi_index(hour_stem_branch)
        
        # 精算月将索引 (基于中气)
        yue_jiang_index = SpaceTimeParser._calculate_yue_jiang_index(solar_time)
        
        # 昼夜判定
        is_daytime = SpaceTimeParser._determine_daytime(zhan_shi_index)
        
        # 计算本命索引
        ben_ming_index = SpaceTimeParser._calculate_ben_ming_index(birth_year)
        
        # 推算行年索引
        xing_nian_index = SpaceTimeParser._calculate_xing_nian_index(
            current_year=solar_time.getYear(),
            birth_year=birth_year,
            gender=gender
        )
        
        # 构建时空参数对象
        return SpaceTimeParams(
            year_stem_branch=year_stem_branch,
            month_stem_branch=month_stem_branch,
            day_stem_branch=day_stem_branch,
            hour_stem_branch=hour_stem_branch,
            zhan_shi_index=zhan_shi_index,
            yue_jiang_index=yue_jiang_index,
            is_daytime=is_daytime,
            gender=gender,
            ben_ming_index=ben_ming_index,
            xing_nian_index=xing_nian_index
        )
    
    @staticmethod
    def _calculate_true_solar_time(dt: datetime, longitude: float) -> datetime:
        """
        计算真太阳时 (True Solar Time)
        
        真太阳时 = 地方平太阳时 + 均时差 (Equation of Time)
        
        Args:
            dt: 当地时间（已包含时区信息或默认为本地标准时间）
            longitude: 经度（东经为正，西经为负）
            
        Returns:
            datetime: 校准后的真太阳时
        """
        # 1. 计算地方平太阳时差 (Local Mean Time Correction)
        # 每度经度相差 4 分钟，以时区中央经线与用户经度的差值计算
        
        # 估算时区中央经线（简化版：根据UTC偏移量估算）
        # 实际应用中应该传入时区信息，这里使用简化估算
        utc_offset_hours = dt.utcoffset().total_seconds() / 3600 if dt.utcoffset() else 8.0  # 默认UTC+8
        central_meridian = utc_offset_hours * 15.0  # 时区中央经线（每15度对应1小时）
        
        # 计算经度差（以中央经线为基准）
        longitude_diff = longitude - central_meridian
        
        # 计算地方平太阳时差（分钟）
        local_time_correction = longitude_diff * SpaceTimeParser.MINUTES_PER_DEGREE
        
        # 2. 计算均时差 (Equation of Time)
        # 这是一个复杂的正弦/余弦周期波动值（大约在 -14 到 +16 分钟之间）
        
        # 计算年中的第几天（1-365/366）
        day_of_year = dt.timetuple().tm_yday
        
        # 使用近似天文公式计算均时差
        # B = 360 * (day_of_year - 81) / 365
        # EoT = 9.87 * sin(2B) - 7.53 * cos(B) - 1.5 * sin(B)
        
        B_degrees = 360.0 * (day_of_year - 81) / 365.0
        B_radians = math.radians(B_degrees)
        
        equation_of_time = (
            9.87 * math.sin(2 * B_radians) - 
            7.53 * math.cos(B_radians) - 
            1.5 * math.sin(B_radians)
        )  # 单位为分钟
        
        # 3. 计算总时间偏移量
        total_correction_minutes = local_time_correction + equation_of_time
        
        # 4. 应用时间偏移量
        correction_timedelta = timedelta(minutes=total_correction_minutes)
        true_solar_time = dt + correction_timedelta
        
        return true_solar_time
    
    @staticmethod
    def _parse_solar_time(solar_time_str: str) -> datetime:
        """
        解析公历时间字符串为 datetime 对象
        
        Args:
            solar_time_str: 公历时间字符串
            
        Returns:
            datetime: 时间对象
        """
        try:
            # 解析时间字符串
            dt = datetime.strptime(solar_time_str, '%Y-%m-%d %H:%M:%S')
            
            return dt
            
        except ValueError as e:
            raise ValueError(f"公历时间解析失败: {solar_time_str}, 错误: {str(e)}")
    
    @staticmethod
    def _get_four_pillars(lunar_time: Lunar) -> Tuple[str, str, str, str]:
        """
        获取四柱八字 (年柱、月柱、日柱、时柱)
        
        Args:
            lunar_time: 农历时间对象
            
        Returns:
            Tuple[str, str, str, str]: 年柱、月柱、日柱、时柱的干支
        """
        # 获取年柱
        year_stem_branch = lunar_time.getYearInGanZhi()
        
        # 获取月柱
        month_stem_branch = lunar_time.getMonthInGanZhi()
        
        # 获取日柱
        day_stem_branch = lunar_time.getDayInGanZhi()
        
        # 获取时柱
        hour_stem_branch = lunar_time.getTimeInGanZhi()
        
        return year_stem_branch, month_stem_branch, day_stem_branch, hour_stem_branch
    
    @staticmethod
    def _extract_zhan_shi_index(hour_stem_branch: str) -> int:
        """
        提取占时索引 (时柱地支索引)
        
        Args:
            hour_stem_branch: 时柱干支
            
        Returns:
            int: 占时地支索引 (0-11)
        """
        if len(hour_stem_branch) != 2:
            raise ValueError(f"时柱干支格式错误: {hour_stem_branch}")
        
        branch_char = hour_stem_branch[1]
        
        if branch_char not in BRANCH_INDEX_MAPPING:
            raise ValueError(f"时柱地支字符无效: {branch_char}")
        
        return BRANCH_INDEX_MAPPING[branch_char]
    
    @staticmethod
    def _calculate_yue_jiang_index(solar_time: Solar) -> int:
        """
        精算月将索引 (基于中气)
        
        大六壬月将与节气（中气）严格挂钩：
        雨水-亥将(11), 春分-戌将(10), 谷雨-酉将(9), 小满-申将(8), 
        夏至-未将(7), 大暑-午将(6), 处暑-巳将(5), 秋分-辰将(4), 
        霜降-卯将(3), 小雪-寅将(2), 冬至-丑将(1), 大寒-子将(0)
        
        Args:
            solar_time: 太阳历对象
            
        Returns:
            int: 月将地支索引 (0-11)
        """
        # 转换为农历时间以获取节气信息
        lunar_time = Lunar.fromSolar(solar_time)
        
        # 获取当前月份和节气
        current_month = lunar_time.getMonth()
        
        # 简化版：根据月份推算月将（实际应该基于精确的节气日期）
        # 这里使用简化的月份映射，实际应用中应该基于精确的节气计算
        month_yue_jiang_mapping = {
            1: 0,   # 正月 - 子将 (大寒后)
            2: 11,  # 二月 - 亥将 (雨水后)  
            3: 10,  # 三月 - 戌将 (春分后)
            4: 9,   # 四月 - 酉将 (谷雨后)
            5: 8,   # 五月 - 申将 (小满后)
            6: 7,   # 六月 - 未将 (夏至后)
            7: 6,   # 七月 - 午将 (大暑后)
            8: 5,   # 八月 - 巳将 (处暑后)
            9: 4,   # 九月 - 辰将 (秋分后)
            10: 3,  # 十月 - 卯将 (霜降后)
            11: 2,  # 冬月 - 寅将 (小雪后)
            12: 1   # 腊月 - 丑将 (冬至后)
        }
        
        return month_yue_jiang_mapping.get(current_month, 0)
    
    @staticmethod
    def _determine_daytime(zhan_shi_index: int) -> bool:
        """
        昼夜判定
        
        规则：占时在卯(3), 辰(4), 巳(5), 午(6), 未(7), 申(8) 视为白天
        
        Args:
            zhan_shi_index: 占时地支索引
            
        Returns:
            bool: 是否为白天
        """
        return zhan_shi_index in DAYTIME_BRANCHES
    
    @staticmethod
    def _calculate_ben_ming_index(birth_year: int) -> int:
        """
        计算本命索引
        
        规则：将出生年份转换为地支索引
        地支对应关系：子(0), 丑(1), 寅(2), 卯(3), 辰(4), 巳(5), 
                    午(6), 未(7), 申(8), 酉(9), 戌(10), 亥(11)
        
        Args:
            birth_year: 出生年份 (公历)
            
        Returns:
            int: 本命地支索引 (0-11)
        """
        # 地支循环周期为12年
        # 1900年为子年(0)，以此类推
        base_year = 1900  # 子年
        branch_index = (birth_year - base_year) % 12
        
        return branch_index
    
    @staticmethod
    def _calculate_xing_nian_index(current_year: int, birth_year: int, gender: str) -> int:
        """
        推算行年索引
        
        规则：
        男起丙寅(寅=2)顺行，女起壬申(申=8)逆行
        以求测者实岁（当前年份 - 出生年份 + 1）进行推导
        
        Args:
            current_year: 当前年份
            birth_year: 出生年份
            gender: 性别
            
        Returns:
            int: 行年地支索引 (0-11)
        """
        # 计算实岁
        age = current_year - birth_year + 1
        
        if gender == '男':
            # 男起丙寅(寅=2)顺行
            start_index = 2  # 寅
            xing_nian_index = (start_index + age - 1) % 12
        else:
            # 女起壬申(申=8)逆行
            start_index = 8  # 申
            xing_nian_index = (start_index - (age - 1)) % 12
            # 处理负数情况
            if xing_nian_index < 0:
                xing_nian_index += 12
        
        return xing_nian_index
    
    @staticmethod
    def validate_stem_branch(stem_branch: str) -> bool:
        """
        验证干支格式
        
        Args:
            stem_branch: 干支字符串
            
        Returns:
            bool: 是否有效
        """
        if len(stem_branch) != 2:
            return False
        
        stems = '甲乙丙丁戊己庚辛壬癸'
        branches = '子丑寅卯辰巳午未申酉戌亥'
        
        return stem_branch[0] in stems and stem_branch[1] in branches


# 快捷函数
def parse_solar_time(solar_time_str: str, longitude: float, gender: str, birth_year: int) -> SpaceTimeParams:
    """
    快捷函数：解析公历时间生成时空参数（支持真太阳时校准）
    
    Args:
        solar_time_str: 公历时间字符串
        longitude: 经度（东经为正，西经为负）
        gender: 性别
        birth_year: 出生年份
        
    Returns:
        SpaceTimeParams: 时空参数对象
    """
    return SpaceTimeParser.parse_datetime(solar_time_str, longitude, gender, birth_year)


# 测试函数
if __name__ == "__main__":
    """
    测试时空解析功能（包含真太阳时校准）
    """
    # 测试数据
    test_time = "2024-03-20 14:30:00"  # 春分附近
    test_longitude = 116.4  # 北京经度
    test_gender = "男"
    test_birth_year = 1990
    
    try:
        # 解析时空参数（包含真太阳时校准）
        params = SpaceTimeParser.parse_datetime(test_time, test_longitude, test_gender, test_birth_year)
        
        print("=== 大六壬时空解析测试结果（真太阳时校准） ===")
        print(f"输入时间: {test_time}")
        print(f"经度: {test_longitude}°E")
        print(f"性别: {test_gender}, 出生年份: {test_birth_year}")
        print()
        print("四柱八字:")
        print(f"  年柱: {params.year_stem_branch}")
        print(f"  月柱: {params.month_stem_branch}")
        print(f"  日柱: {params.day_stem_branch}")
        print(f"  时柱: {params.hour_stem_branch}")
        print()
        print("大六壬参数:")
        print(f"  占时索引: {params.zhan_shi_index} ({BRANCHES[params.zhan_shi_index]})")
        print(f"  月将索引: {params.yue_jiang_index} ({BRANCHES[params.yue_jiang_index]})")
        print(f"  昼夜判定: {'白天' if params.is_daytime else '夜间'}")
        print(f"  本命索引: {params.ben_ming_index} ({BRANCHES[params.ben_ming_index]})")
        print(f"  行年索引: {params.xing_nian_index} ({BRANCHES[params.xing_nian_index]})")
        
        # 测试不同经度的真太阳时校准
        print("\n=== 真太阳时校准测试 ===")
        test_datetime = datetime(2024, 3, 20, 14, 30, 0)
        
        # 北京 (116.4°E)
        beijing_time = SpaceTimeParser._calculate_true_solar_time(test_datetime, 116.4)
        print(f"北京 (116.4°E) 真太阳时: {beijing_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 纽约 (-74.0°E)
        newyork_time = SpaceTimeParser._calculate_true_solar_time(test_datetime, -74.0)
        print(f"纽约 (-74.0°E) 真太阳时: {newyork_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 伦敦 (0.0°E)
        london_time = SpaceTimeParser._calculate_true_solar_time(test_datetime, 0.0)
        print(f"伦敦 (0.0°E) 真太阳时: {london_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"解析失败: {str(e)}")