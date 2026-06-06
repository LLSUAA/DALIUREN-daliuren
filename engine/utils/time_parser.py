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


# ============================================================
#  天文学均时差 (Equation of Time) 计算模块
#  基于斯宾塞 (Spencer, 1971) 傅里叶级数展开公式
#  实现绝对精确的真太阳时校准
# ============================================================

def calculate_equation_of_time_spencer(day_of_year: int, year: int = 2024) -> float:
    """
    基于斯宾塞 (Spencer, 1971) 公式计算均时差 (Equation of Time)

    均时差是真太阳时与平太阳时之间的差值，由地球轨道的椭圆率和自转轴倾角引起。
    该函数使用斯宾塞提出的傅里叶级数展开公式，精度可达 ±0.01 分钟数量级，
    广泛用于太阳能工程、天文历算等领域。

    天文学背景：
    - 均时差范围约在 -14.2 到 +16.4 分钟之间
    - 产生原因有两个独立的天文效应：
      ① 黄赤交角（ε≈23.44°）：导致太阳在黄道上的不均匀运动投影到天赤道
      ② 地球轨道偏心率（e≈0.0167）：导致地球公转角速度的季节性变化
    - 全年呈现双峰双谷的周期性波动曲线

    Args:
        day_of_year: 年积日 (1-365/366)，1月1日为第1天
        year: 公历年份，用于闰年边界校验（不影响核心公式的365天基准）

    Returns:
        float: 均时差（分钟），正值表示真太阳时快于平太阳时

    Raises:
        ValueError: 年积日超出合法范围时抛出

    References:
        Spencer, J.W. (1971). "Fourier series representation of the position of
        the Sun." Search, 2(5), 172.

        NOAA Solar Calculator Documentation:
        https://gml.noaa.gov/grad/solcalc/solareqns.PDF

    Example:
        >>> eot = calculate_equation_of_time_spencer(day_of_year=80, year=2024)
        >>> print(f"春分附近的均时差: {eot:.2f} 分钟")
        >>> # 全年最大正值通常在11月初，最大负值通常在2月中旬
    """
    # --- 输入验证 ---
    if not isinstance(day_of_year, int):
        raise TypeError(f"年积日必须为整数类型，当前类型: {type(day_of_year).__name__}")

    if not 1 <= day_of_year <= 366:
        raise ValueError(f"年积日必须在 1-366 之间，当前值: {day_of_year}")

    # 闰年判断（格里高利历规则）
    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    max_days = 366 if is_leap else 365

    if day_of_year > max_days:
        raise ValueError(
            f"年积日 {day_of_year} 超出 {year} 年最大天数 {max_days} "
            f"({'闰' if is_leap else '平'}年)"
        )

    # --- Spencer 公式核心计算 ---
    # 将年积日转换为轨道角度 B（弧度制）
    # B = 2π * (day_of_year - 1) / 365.0
    # 注意：Spencer 原公式使用固定 365 天作为周期基准，不区分平闰年
    B_radians = 2.0 * math.pi * (day_of_year - 1) / 365.0

    # Spencer (1971) 傅里叶级数形式的均时差公式
    #
    # EoT = 229.18 * [
    #     0.000075                          # C0: 常数项（微小的零点偏移）
    #     + 0.001868 * cos(B)               # C1_cos: 一次余弦项
    #     - 0.032077 * sin(B)               # C1_sin: 一次正弦项（主要项）
    #     - 0.014615 * cos(2B)              # C2_cos: 二次余弦项
    #     - 0.040849 * sin(2B)              # C2_sin: 二次正弦项（主要项）
    # ]
    #
    # 系数物理含义：
    #   一次项 (sin B, cos B)：由地球轨道偏心率主导，周期1年
    #   二次项 (sin 2B, cos 2B)：由黄赤交角与偏心率的高阶耦合产生，周期半年
    #   常数因子 229.18 = 1440 / (2π)：将弧度单位下的角度差转换为时间分钟

    equation_of_time = 229.18 * (
        0.000075
        + 0.001868 * math.cos(B_radians)
        - 0.032077 * math.sin(B_radians)
        - 0.014615 * math.cos(2.0 * B_radians)
        - 0.040849 * math.sin(2.0 * B_radians)
    )

    return equation_of_time


def get_true_solar_time(beijing_time_str: str, longitude: float) -> datetime:
    """
    计算绝对精确的真太阳时 (True Solar Time)

    将北京时间（UTC+8，以东经120°为中央经线）转换为观测点的
    真太阳时。综合考虑经度平差和均时差两项修正。

    计算流程：
    ┌─────────────────────────────────────────────────────┐
    │  真太阳时 = 北京时间 + 经度平差 + 均时差(EoT)      │
    │                                                     │
    │  经度平差 = (观测经度 - 120°) × 4 分钟/度          │
    │  均时差   = Spencer 公式计算结果                     │
    └─────────────────────────────────────────────────────┘

    大六壬应用背景：
    大六壬起课以真太阳时为准。古代以日晷测定时刻，即为真太阳时。
    现代使用北京时间（平太阳时），需经此函数修正后方可用于起课。
    尤其是经度偏离120°较多的地区（如新疆、西藏），修正量可达
    1小时以上，对时柱地支判定影响重大。

    Args:
        beijing_time_str: 北京时间字符串，格式 "YYYY-MM-DD HH:MM:SS"
                          例如 "2024-03-20 14:30:00"
        longitude: 观测点经度（东经为正，西经为负）
                   例如北京约 116.4°，乌鲁木齐约 87.6°

    Returns:
        datetime: 修正后的真太阳时 datetime 对象

    Raises:
        ValueError: 当时间字符串格式无效或经度超出范围时抛出
        TypeError: 当参数类型不正确时抛出

    Example:
        >>> # 北京 (116.4°E) 春分下午的真太阳时
        >>> true_time = get_true_solar_time("2024-03-20 14:30:00", 116.4)
        >>> print(f"北京真太阳时: {true_time.strftime('%Y-%m-%d %H:%M:%S')}")
        >>>
        >>> # 乌鲁木齐 (87.6°E) 正午的真太阳时
        >>> urumqi = get_true_solar_time("2024-06-21 12:00:00", 87.6)
        >>> print(f"乌鲁木齐真太阳时: {urumqi.strftime('%Y-%m-%d %H:%M:%S')}")
    """
    # --- 输入验证 ---
    if not isinstance(beijing_time_str, str):
        raise TypeError(
            f"北京时间参数必须为字符串类型，当前类型: {type(beijing_time_str).__name__}"
        )

    if not isinstance(longitude, (int, float)):
        raise TypeError(
            f"经度参数必须为数值类型，当前类型: {type(longitude).__name__}"
        )

    if not -180.0 <= longitude <= 180.0:
        raise ValueError(f"经度必须在 -180° 到 180° 之间，当前值: {longitude}")

    # --- 解析北京时间字符串 ---
    try:
        beijing_time = datetime.strptime(beijing_time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        raise ValueError(
            f"北京时间格式解析失败，需要格式 YYYY-MM-DD HH:MM:SS，"
            f"实际输入: '{beijing_time_str}'"
        ) from e

    # --- 计算年积日（用于均时差计算） ---
    day_of_year = beijing_time.timetuple().tm_yday

    # --- 第一步：经度平差 ---
    # 东八区（北京时间）中央经线为东经 120°
    # 观测点每偏西1度，真太阳时慢4分钟；每偏东1度，真太阳时快4分钟
    BEIJING_CENTRAL_MERIDIAN = 120.0  # 东八区中央经线 (120°E)
    MINUTES_PER_DEGREE = 4.0  # 每度经度对应4分钟时差

    longitude_correction = (
        (longitude - BEIJING_CENTRAL_MERIDIAN) * MINUTES_PER_DEGREE
    )  # 单位：分钟

    # --- 第二步：均时差 (Equation of Time) ---
    # 使用斯宾塞公式精确计算当日均时差
    equation_of_time = calculate_equation_of_time_spencer(
        day_of_year, beijing_time.year
    )

    # --- 第三步：合成真太阳时 ---
    total_correction_minutes = longitude_correction + equation_of_time
    true_solar_time = beijing_time + timedelta(minutes=total_correction_minutes)

    return true_solar_time


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

        地方平太阳时基于经度与所在时区中央经线的差值修正，
        均时差基于斯宾塞 (Spencer, 1971) 傅里叶级数公式计算。

        该方法为 SpaceTimeParser 内部使用，外部调用请使用模块级函数
        get_true_solar_time() 以获得更友好的接口。

        Args:
            dt: 当地时间 datetime 对象（应已包含正确的时区信息）
            longitude: 经度（东经为正，西经为负）

        Returns:
            datetime: 校准后的真太阳时

        Raises:
            ValueError: 经度超出合法范围时抛出
        """
        # --- 输入验证 ---
        if not -180.0 <= longitude <= 180.0:
            raise ValueError(f"经度必须在 -180° 到 180° 之间，当前值: {longitude}")

        # ===============================================
        #   第一部分：经度平差 (Longitude Correction)
        # ===============================================
        # 推算时区中央经线
        # 原理：每个时区跨15°经度，中央经线 = UTC偏移小时数 × 15°
        if dt.utcoffset() is not None:
            utc_offset_hours = dt.utcoffset().total_seconds() / 3600.0
        else:
            # 若无时区信息，默认东八区（北京时间）
            utc_offset_hours = 8.0

        central_meridian = utc_offset_hours * 15.0  # 时区中央经线

        # 观测点与中央经线的经度差
        longitude_diff = longitude - central_meridian

        # 经度平差（分钟）：每度经度差对应4分钟时差
        longitude_time_correction = (
            longitude_diff * SpaceTimeParser.MINUTES_PER_DEGREE
        )

        # ===============================================
        #   第二部分：均时差 (Equation of Time)
        # ===============================================
        # 获取年积日用于均时差计算
        day_of_year = dt.timetuple().tm_yday

        # 调用斯宾塞公式精确计算当日均时差
        equation_of_time = calculate_equation_of_time_spencer(
            day_of_year, dt.year
        )

        # ===============================================
        #   第三部分：合成真太阳时
        # ===============================================
        total_correction_minutes = longitude_time_correction + equation_of_time
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
        精算月将索引 (基于精确中气算法)
        
        大六壬月将与节气（中气）严格挂钩：
        雨水-亥将(11), 春分-戌将(10), 谷雨-酉将(9), 小满-申将(8), 
        夏至-未将(7), 大暑-午将(6), 处暑-巳将(5), 秋分-辰将(4), 
        霜降-卯将(3), 小雪-寅将(2), 冬至-丑将(1), 大寒-子将(0)
        
        算法原理：
        月将即太阳过宫之所，以十二中气为分界点。当前时间所处的中气区间
        由上一个已过去的中气决定。例如雨水后、春分前为亥将。
        
        Args:
            solar_time: 太阳历对象
            
        Returns:
            int: 月将地支索引 (0-11)
        """
        # 转换为农历时间以获取节气信息
        lunar_time = Lunar.fromSolar(solar_time)
        
        # 获取上一个中气的名称（如"雨水"、"春分"等）
        prev_zhong_qi = lunar_time.getPrevQi()
        zhong_qi_name = prev_zhong_qi.getName()
        
        # 利用中气->月将映射字典获取正确的月将索引
        if zhong_qi_name in SOLAR_TERM_YUE_JIANG:
            return SOLAR_TERM_YUE_JIANG[zhong_qi_name]
        
        # 兜底：如遇未知中气名称，回退到大寒
        return SOLAR_TERM_YUE_JIANG.get('大寒', 0)
    
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
    验证斯宾塞公式均时差计算和 get_true_solar_time 主函数
    """
    # ===========================================
    #   测试一：斯宾塞均时差公式计算
    # ===========================================
    print("╔══════════════════════════════════════════════════╗")
    print("║      斯宾塞 (Spencer) 均时差公式测试              ║")
    print("╚══════════════════════════════════════════════════╝")

    # 选取四个关键日期节点验证均时差曲线
    test_dates_eot = [
        (1, "1月1日（近日点附近）"),
        (80, "3月21日（春分附近）"),
        (172, "6月21日（夏至附近）"),
        (266, "9月23日（秋分附近）"),
        (355, "12月21日（冬至附近）"),
    ]

    for day, desc in test_dates_eot:
        eot = calculate_equation_of_time_spencer(day, 2024)
        direction = "快于" if eot > 0 else "慢于"
        print(f"  {desc:30s} | 年积日 {day:3d} | "
              f"均时差 = {eot:+.2f} 分钟 (真太阳时 {direction} 平太阳时)")

    print()
    print(f"  全年均时差范围：[{calculate_equation_of_time_spencer(46, 2024):.1f}, "
          f"{calculate_equation_of_time_spencer(309, 2024):.1f}] 分钟")
    print(f"  理论范围参考：[-14.2, +16.4] 分钟")

    # ===========================================
    #   测试二：get_true_solar_time 主函数
    # ===========================================
    print("\n╔══════════════════════════════════════════════════╗")
    print("║      get_true_solar_time() 主函数测试             ║")
    print("╚══════════════════════════════════════════════════╝")

    test_time = "2024-03-20 14:30:00"  # 春分附近

    # 测试不同城市的真太阳时
    cities = [
        ("北京", 116.4, "东经116.4°"),
        ("上海", 121.5, "东经121.5°"),
        ("乌鲁木齐", 87.6, "东经87.6°"),
        ("拉萨", 91.1, "东经91.1°"),
        ("哈尔滨", 126.6, "东经126.6°"),
    ]

    beijing_dt = datetime.strptime(test_time, '%Y-%m-%d %H:%M:%S')
    day_of_year = beijing_dt.timetuple().tm_yday

    for city_name, lon, desc in cities:
        true_solar = get_true_solar_time(test_time, lon)
        # 计算各项修正的贡献
        lon_corr = (lon - 120.0) * 4.0
        eot_corr = calculate_equation_of_time_spencer(day_of_year, 2024)
        total_corr = lon_corr + eot_corr
        print(f"\n  📍 {city_name} ({desc})")
        print(f"     输入北京时间:     {test_time}")
        print(f"     经度平差:          {lon_corr:+.2f} 分钟")
        print(f"     均时差(EoT):       {eot_corr:+.2f} 分钟")
        print(f"     总修正量:          {total_corr:+.2f} 分钟 "
              f"({total_corr / 60.0:+.2f} 小时)")
        print(f"     真太阳时:          {true_solar.strftime('%Y-%m-%d %H:%M:%S')}")

    # ===========================================
    #   测试三：异常处理验证
    # ===========================================
    print("\n╔══════════════════════════════════════════════════╗")
    print("║         异常处理与边界条件测试                    ║")
    print("╚══════════════════════════════════════════════════╝")

    # 测试无效时间格式
    try:
        get_true_solar_time("2024-13-01 12:00:00", 116.4)
        print("  ✗ 应该抛出异常但未抛出")
    except ValueError as e:
        print(f"  ✓ 无效月份被正确拦截: {e}")

    # 测试无效经度
    try:
        get_true_solar_time("2024-03-20 12:00:00", 200.0)
        print("  ✗ 应该抛出异常但未抛出")
    except ValueError as e:
        print(f"  ✓ 经度超限被正确拦截: {e}")

    # 测试平年2月29日（非闰年）
    try:
        calculate_equation_of_time_spencer(366, 2023)  # 2023不是闰年
        print("  ✗ 应该抛出异常但未抛出")
    except ValueError as e:
        print(f"  ✓ 平年366天被正确拦截: {e}")

    # 测试年积日边界
    try:
        calculate_equation_of_time_spencer(0, 2024)
        print("  ✗ 应该抛出异常但未抛出")
    except ValueError as e:
        print(f"  ✓ 年积日≤0被正确拦截: {e}")

    # ===========================================
    #   测试四：SpaceTimeParser 完整集成测试
    # ===========================================
    print("\n╔══════════════════════════════════════════════════╗")
    print("║     SpaceTimeParser 完整时空解析测试              ║")
    print("╚══════════════════════════════════════════════════╝")

    test_longitude = 116.4  # 北京经度
    test_gender = "男"
    test_birth_year = 1990

    try:
        params = SpaceTimeParser.parse_datetime(
            test_time, test_longitude, test_gender, test_birth_year
        )

        print(f"  输入时间: {test_time}")
        print(f"  经度: {test_longitude}°E")
        print(f"  性别: {test_gender}, 出生年份: {test_birth_year}")
        print()
        print("  四柱八字:")
        print(f"    年柱: {params.year_stem_branch}")
        print(f"    月柱: {params.month_stem_branch}")
        print(f"    日柱: {params.day_stem_branch}")
        print(f"    时柱: {params.hour_stem_branch}")
        print()
        print("  大六壬参数:")
        print(f"    占时索引: {params.zhan_shi_index} "
              f"({BRANCHES[params.zhan_shi_index]})")
        print(f"    月将索引: {params.yue_jiang_index} "
              f"({BRANCHES[params.yue_jiang_index]})")
        print(f"    昼夜判定: {'白天 ☀️' if params.is_daytime else '夜间 🌙'}")
        print(f"    本命索引: {params.ben_ming_index} "
              f"({BRANCHES[params.ben_ming_index]})")
        print(f"    行年索引: {params.xing_nian_index} "
              f"({BRANCHES[params.xing_nian_index]})")

    except Exception as e:
        print(f"  ✗ 解析失败: {str(e)}")

    print("\n" + "=" * 52)
    print("  所有测试完成 ✅")
    print("=" * 52)