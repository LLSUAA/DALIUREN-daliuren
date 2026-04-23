"""
大六壬物理引擎 - 时空参数数据模型
定义推演所需的完整时空参数结构
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class SpaceTimeParams(BaseModel):
    """
    时空参数数据类
    包含大六壬推演所需的完整时空信息
    
    Attributes:
        year_stem_branch: 年柱干支，如"甲子"
        month_stem_branch: 月柱干支，如"乙丑"
        day_stem_branch: 日柱干支，如"丙寅"
        hour_stem_branch: 时柱干支，如"丁卯"
        zhan_shi_index: 占时地支索引 (0-11)
        yue_jiang_index: 月将地支索引 (0-11)
        is_daytime: 是否为白天 (用于排布十二天将)
        gender: 性别 ("男" 或 "女")
        ben_ming_index: 本命地支索引 (0-11)
        xing_nian_index: 行年地支索引 (0-11)
    """
    
    # 四柱八字
    year_stem_branch: str = Field(..., min_length=2, max_length=2, description="年柱干支")
    month_stem_branch: str = Field(..., min_length=2, max_length=2, description="月柱干支")
    day_stem_branch: str = Field(..., min_length=2, max_length=2, description="日柱干支")
    hour_stem_branch: str = Field(..., min_length=2, max_length=2, description="时柱干支")
    
    # 大六壬核心参数
    zhan_shi_index: int = Field(..., ge=0, le=11, description="占时地支索引 (0-11)")
    yue_jiang_index: int = Field(..., ge=0, le=11, description="月将地支索引 (0-11)")
    is_daytime: bool = Field(..., description="是否为白天 (用于排布十二天将)")
    
    # 个人信息
    gender: str = Field(..., description="性别 (男/女)")
    ben_ming_index: int = Field(..., ge=0, le=11, description="本命地支索引 (0-11)")
    xing_nian_index: int = Field(..., ge=0, le=11, description="行年地支索引 (0-11)")
    
    @validator('year_stem_branch', 'month_stem_branch', 'day_stem_branch', 'hour_stem_branch')
    def validate_stem_branch(cls, v):
        """验证干支格式"""
        if len(v) != 2:
            raise ValueError(f"干支必须为2个字符，当前值: {v}")
        
        # 天干验证 (甲乙丙丁戊己庚辛壬癸)
        stems = '甲乙丙丁戊己庚辛壬癸'
        if v[0] not in stems:
            raise ValueError(f"天干字符无效，必须是{stems}中的一个，当前值: {v[0]}")
        
        # 地支验证 (子丑寅卯辰巳午未申酉戌亥)
        branches = '子丑寅卯辰巳午未申酉戌亥'
        if v[1] not in branches:
            raise ValueError(f"地支字符无效，必须是{branches}中的一个，当前值: {v[1]}")
        
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        """验证性别"""
        if v not in ['男', '女']:
            raise ValueError(f"性别必须是'男'或'女'，当前值: {v}")
        return v
    
    @validator('zhan_shi_index', 'yue_jiang_index', 'ben_ming_index', 'xing_nian_index')
    def validate_branch_index(cls, v):
        """验证地支索引"""
        if not 0 <= v <= 11:
            raise ValueError(f"地支索引必须在0-11范围内，当前值: {v}")
        return v
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'year_stem_branch': self.year_stem_branch,
            'month_stem_branch': self.month_stem_branch,
            'day_stem_branch': self.day_stem_branch,
            'hour_stem_branch': self.hour_stem_branch,
            'zhan_shi_index': self.zhan_shi_index,
            'yue_jiang_index': self.yue_jiang_index,
            'is_daytime': self.is_daytime,
            'gender': self.gender,
            'ben_ming_index': self.ben_ming_index,
            'xing_nian_index': self.xing_nian_index
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SpaceTimeParams':
        """从字典创建实例"""
        return cls(**data)


class SolarTimeInput(BaseModel):
    """
    太阳历时间输入模型
    用于接收前端传入的时间参数
    
    Attributes:
        solar_time_str: 公历时间字符串 (YYYY-MM-DD HH:MM:SS)
        gender: 性别 ("男" 或 "女")
        birth_year: 出生年份 (公历)
    """
    
    solar_time_str: str = Field(..., description="公历时间字符串 (YYYY-MM-DD HH:MM:SS)")
    gender: str = Field(..., description="性别 (男/女)")
    birth_year: int = Field(..., ge=1900, le=2100, description="出生年份 (公历)")
    
    @validator('solar_time_str')
    def validate_solar_time(cls, v):
        """验证公历时间格式"""
        import re
        pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        if not re.match(pattern, v):
            raise ValueError(f"时间格式必须为 YYYY-MM-DD HH:MM:SS，当前值: {v}")
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        """验证性别"""
        if v not in ['男', '女']:
            raise ValueError(f"性别必须是'男'或'女'，当前值: {v}")
        return v


# 地支索引映射表
BRANCH_INDEX_MAPPING = {
    '子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5,
    '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11
}

# 地支字符列表
BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 天干字符列表
STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

# 月将节气映射表 (中气 -> 月将索引)
SOLAR_TERM_YUE_JIANG = {
    '雨水': 11,  # 亥将
    '春分': 10,  # 戌将
    '谷雨': 9,   # 酉将
    '小满': 8,   # 申将
    '夏至': 7,   # 未将
    '大暑': 6,   # 午将
    '处暑': 5,   # 巳将
    '秋分': 4,   # 辰将
    '霜降': 3,   # 卯将
    '小雪': 2,   # 寅将
    '冬至': 1,   # 丑将
    '大寒': 0    # 子将
}

# 白天地支索引 (卯辰巳午未申)
DAYTIME_BRANCHES = {3, 4, 5, 6, 7, 8}