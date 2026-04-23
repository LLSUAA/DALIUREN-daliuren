"""
大六壬赛博终端 - FastAPI后端接口
提供与Vue前端对接的API服务，支持真太阳时时空推演
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Any
from pydantic import BaseModel

# 导入大六壬引擎和时空解析器
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import DaLiuRenEngine
from engine.utils.time_parser import SpaceTimeParser
from engine.utils.oracle import generate_reading


# 天干地支映射字典
STEM_MAPPING = {
    '甲': 0, '乙': 1, '丙': 2, '丁': 3, '戊': 4,
    '己': 5, '庚': 6, '辛': 7, '壬': 8, '癸': 9
}

BRANCH_MAPPING = {
    '子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4,
    '巳': 5, '午': 6, '未': 7, '申': 8, '酉': 9,
    '戌': 10, '亥': 11
}

# 地支字符列表
BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']


class DeduceRequest(BaseModel):
    """时空推演请求参数模型"""
    time_str: str  # 格式 "YYYY-MM-DD HH:MM:SS"
    longitude: float  # 经度（东经为正，西经为负）
    gender: str  # "男" 或 "女"
    birth_year: int  # 出生年份
    event_intent: str  # 占测事由


class DeduceResponse(BaseModel):
    """推演响应模型"""
    success: bool
    snapshot: Dict[str, Any] = None
    error: str = None
    route_warning: str = None


# 创建FastAPI应用实例
app = FastAPI(
    title="大六壬赛博终端API",
    description="提供大六壬推演服务的后端接口",
    version="1.0.0"
)

# 🚀 加上这层跨域护盾！(允许 Tauri 的前端随意访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 桌面本地应用，直接放行所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def root():
    """根路径，返回服务状态"""
    return {
        "status": "running",
        "service": "大六壬赛博终端API",
        "version": "1.0.0"
    }


@app.post("/api/deduce", response_model=DeduceResponse)
async def deduce(request: DeduceRequest) -> DeduceResponse:
    """
    大六壬时空推演接口（支持真太阳时）
    
    Args:
        request: 时空推演请求参数
        
    Returns:
        DeduceResponse: 推演结果和时空参数信息
    """
    try:
        # 调用时空解析器获取完整参数
        params = SpaceTimeParser.parse_datetime(
            solar_time_str=request.time_str,
            longitude=request.longitude,
            gender=request.gender,
            birth_year=request.birth_year
        )
        
        # 从日柱干支中提取天干地支索引
        day_stem_char = params.day_stem_branch[0]  # 天干字符
        day_branch_char = params.day_stem_branch[1]  # 地支字符
        
        day_stem_index = STEM_MAPPING.get(day_stem_char)
        day_branch_index = BRANCH_MAPPING.get(day_branch_char)
        
        if day_stem_index is None or day_branch_index is None:
            raise ValueError(f"日柱干支解析失败: {params.day_stem_branch}")
        
        # 调用大六壬引擎生成快照
        snapshot = DaLiuRenEngine.generate_snapshot(
            zhan_shi_index=params.zhan_shi_index,
            yue_jiang_index=params.yue_jiang_index,
            day_stem_index=day_stem_index,
            day_branch_index=day_branch_index
        )
        
        # 生成路由警告信息
        route_warning = generate_route_warning(snapshot)
        
        # 生成神谕解读
        oracle_reading = await generate_reading(
            intent=request.event_intent,
            snapshot_data=snapshot,
            spacetime_data={
                "four_pillars": {
                    "year": params.year_stem_branch,
                    "month": params.month_stem_branch,
                    "day": params.day_stem_branch,
                    "hour": params.hour_stem_branch
                },
                "ben_ming": BRANCHES[params.ben_ming_index],
                "xing_nian": BRANCHES[params.xing_nian_index],
                "is_daytime": "白天" if params.is_daytime else "夜间",
                "reversal_flags": snapshot.get("reversal_flags", {})
            }
        )
        
        # 构建完整的响应数据
        response_data = {
            "snapshot": snapshot,
            "spacetime_params": {
                "four_pillars": {
                    "year": params.year_stem_branch,
                    "month": params.month_stem_branch,
                    "day": params.day_stem_branch,
                    "hour": params.hour_stem_branch
                },
                "true_solar_time": request.time_str,
                "longitude": request.longitude,
                "gender": params.gender,
                "birth_year": request.birth_year,
                "ben_ming": BRANCHES[params.ben_ming_index],
                "xing_nian": BRANCHES[params.xing_nian_index],
                "is_daytime": "白天" if params.is_daytime else "夜间"
            },
            "event_intent": request.event_intent,
            "route_warning": route_warning,
            "oracle_reading": oracle_reading
        }
        
        return DeduceResponse(
            success=True,
            snapshot=response_data,
            route_warning=route_warning
        )
        
    except ValueError as e:
        # 参数验证错误
        return DeduceResponse(
            success=False,
            error=f"参数验证失败: {str(e)}"
        )
    except Exception as e:
        # 其他错误
        return DeduceResponse(
            success=False,
            error=f"推演过程出错: {str(e)}"
        )


def generate_route_warning(snapshot: Dict[str, Any]) -> str:
    """
    根据推演快照生成路由警告信息
    
    Args:
        snapshot: 推演快照
        
    Returns:
        str: 路由警告信息
    """
    route_decision = snapshot.get("route_decision", {})
    route_method = route_decision.get("method", "Unknown")
    init_lesson_id = route_decision.get("init_node_lesson_id", 0)
    
    # 路由方法映射
    route_methods = {
        "SHE_HAI": "涉害",
        "FU_YIN": "伏吟",
        "FAN_YIN": "反吟",
        "ZEI_KE": "贼克",
        "BI_YONG": "比用",
        "BA_ZHUAN": "八专",
        "DUAN_TUI": "断腿",
        "YANG_ZHANG": "昂张",
        "BING_ZHU": "并著"
    }
    
    method_name = route_methods.get(route_method, route_method)
    
    # 生成警告信息
    warnings = [
        f"[WARNING] 命中路由: {method_name}",
        f"[ANALYZE] 底层极性熔断，崩溃源头：第{init_lesson_id}课",
        f"[PROCESS] 时空矩阵稳定，正在计算三传...",
        f"[INFO] 六壬协议V10.0 - 推演完成"
    ]
    
    # 根据路由方法添加特定警告
    if route_method == "SHE_HAI":
        warnings.insert(1, "[CRITICAL] 检测到涉害冲突，启动深度扫描模式")
    elif route_method == "FU_YIN":
        warnings.insert(1, "[ALERT] 伏吟模式激活，时空场强异常")
    elif route_method == "FAN_YIN":
        warnings.insert(1, "[ALERT] 反吟模式激活，能量反向流动")
    
    return "\n".join(warnings)


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "大六壬赛博终端API"}


if __name__ == "__main__":
    import uvicorn
    # 注意：这里传入的是 app 对象本身，绝不能加引号写成 "server:app"
    # 同时保留 log_config=None 防崩溃护盾
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)