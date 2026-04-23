from typing import List, Optional
from pydantic import BaseModel, Field, validator
from engine.core.constants import EarthlyBranch


class OrbitComp(BaseModel):
    """轨道组件：管理空间矩阵中的位置索引"""
    earth_index: int = Field(..., ge=0, le=11, description="静态底层网格索引，范围0-11")
    heaven_index: int = Field(..., ge=0, le=11, description="动态旋转天盘映射索引，范围0-11")

    @validator('earth_index', 'heaven_index')
    def validate_index_range(cls, v):
        if not 0 <= v <= 11:
            raise ValueError(f"索引值必须在0-11范围内，当前值: {v}")
        return v

    @property
    def earthly_branch(self) -> EarthlyBranch:
        """获取对应的地支枚举"""
        return EarthlyBranch(self.earth_index)

    @property
    def is_aligned(self) -> bool:
        """检查天地盘是否对齐"""
        return self.earth_index == self.heaven_index


class PolityComp(BaseModel):
    """阵营组件：标识系统内外的节点关系"""
    is_host: bool = Field(..., description="是否为系统内/我方节点")
    is_guest: bool = Field(..., description="是否为外部环境/敌方节点")

    @validator('is_guest')
    def validate_polity_consistency(cls, v, values):
        if 'is_host' in values:
            is_host = values['is_host']
            if is_host and v:
                raise ValueError("节点不能同时为host和guest")
            if not is_host and not v:
                raise ValueError("节点必须为host或guest之一")
        return v

    @property
    def polity_type(self) -> str:
        """获取阵营类型"""
        return "host" if self.is_host else "guest"


class ModifierComp(BaseModel):
    """修饰器组件：管理状态改变和效果"""
    modifier_name: str = Field(..., min_length=1, description="属性名称，如'朱雀'")
    modifier_type: str = Field(..., description="修饰器类型，如'debuff', 'buff', 'intercept'")
    effects: List[str] = Field(default_factory=list, description="具体状态改变参数列表")

    @validator('modifier_type')
    def validate_modifier_type(cls, v):
        valid_types = {"debuff", "buff", "intercept", "transform", "shield"}
        if v not in valid_types:
            raise ValueError(f"无效的修饰器类型: {v}，有效类型: {valid_types}")
        return v

    @validator('effects', each_item=True)
    def validate_effects(cls, v):
        if not v or not v.strip():
            raise ValueError("效果参数不能为空")
        return v.strip()

    def add_effect(self, effect: str) -> None:
        """添加效果参数"""
        if effect and effect.strip():
            self.effects.append(effect.strip())

    def clear_effects(self) -> None:
        """清空效果参数"""
        self.effects.clear()