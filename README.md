# 大六壬赛博终端 (Da Liu Ren Cyber Terminal)

> 融合古代东方术数智慧与现代科技美学的跨平台桌面应用

![大六壬赛博终端](liuren-cyber-terminal/src-tauri/icons/icon.png)

## 🌟 项目亮点

### 🎨 **极简科技美学界面**
- **玻璃拟态设计**：半透明背景 + 高斯模糊效果
- **全息天体运行**：500px宏大星盘 + 双重发光核心
- **物理厚重动画**：4秒缓动曲线模拟机械齿轮咬合感
- **赛博风格交互**：自定义自动补全下拉菜单

### 🤖 **工业级推演引擎**
- **硬逻辑计算**：空亡、绝处逢生等关键判断由物理引擎精确计算
- **100%存活保证**：五层降级策略确保引擎永不崩溃
- **专业算法实现**：九宗门路由网关 + 五行生克计算
- **真太阳时校准**：支持全球经纬度的天文时间计算

### 🧠 **AI增强解读系统**
- **结构化提示词**：四段式专业解读模板
- **硬性条件约束**：AI必须遵守物理引擎判定结果
- **深度推演空间**：800 tokens支持完整逻辑推演
- **实用导向输出**：定盘确真 → 推演链条 → 铁断应期 → 风控应对

## 📁 项目结构

```
DALIUREN/
├── api/                           # FastAPI后端服务
│   ├── server.py                  # 主API接口
│   └── main.py                    # 大六壬核心引擎
├── engine/                        # 大六壬物理引擎
│   ├── core/                      # 核心数据模型
│   │   ├── constants.py           # 天干地支映射
│   │   └── schemas.py             # Pydantic数据模型
│   ├── systems/                   # 系统模块
│   │   ├── astrolabe_sys.py       # 天体运行系统
│   │   ├── four_lessons_sys.py    # 四课生成系统
│   │   └── routing_sys.py         # 路由网关系统
│   └── utils/                     # 工具模块
│       ├── time_parser.py         # 时空解析器
│       └── oracle.py              # AI神谕解读
├── liuren-cyber-terminal/         # Tauri+Vue前端
│   ├── src/
│   │   ├── App.vue                # 主界面组件
│   │   └── style.css              # 赛博风格样式
│   └── src-tauri/                 # Tauri桌面应用配置
├── tests/                         # 测试套件
├── backtest.py                    # 自动化回测系统
└── 项目进度汇报.md                # 开发文档
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 18+
- Tauri CLI

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd DALIUREN
```

2. **设置Python环境**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，设置OpenAI API密钥
```

4. **启动后端服务**
```bash
cd api
python server.py
```

5. **启动前端应用**
```bash
cd liuren-cyber-terminal
npm install
npm run tauri dev
```

## 🔧 核心机制解析

### 1. 时空解析系统

**真太阳时校准**：基于天文算法计算真实太阳时间
```python
class SpaceTimeParser:
    def parse_datetime(solar_time_str, longitude, gender, birth_year):
        # 计算时差修正
        time_diff = longitude / 15  # 每15度经度对应1小时
        # 计算均时差
        equation_of_time = self._calculate_equation_of_time(date)
        # 返回校准后的时空参数
```

### 2. 大六壬推演引擎

**九宗门路由网关**：五层降级策略确保100%存活
```python
class RoutingGatewaySystem:
    def dispatch_route(lessons, day_stem_index):
        # 1. 贼克法 → 2. 比用法 → 3. 涉害法
        # 4. 遥克法 → 5. 昴星法（终极兜底）
        
        if len(all_clashes) == 0:  # 无克情况
            # 遥克法降级
            yao_ke_result = self._try_yao_ke_method(lessons, day_stem_index)
            if yao_ke_result:
                return yao_ke_result
            # 昴星法兜底
            return self._fallback_mao_xing_method(lessons)
```

### 3. 硬逻辑计算系统

**神煞与空亡计算**：物理引擎精确判定
```python
class DaLiuRenEngine:
    def _calculate_reversal_flags(day_stem_index, day_branch_index):
        # 计算旬空（空亡）地支
        kong_wang_branches = self._calculate_kong_wang(day_stem_index)
        # 判断绝处逢生
        is_jue_chu_feng_sheng = self._check_jue_chu_feng_sheng(day_stem_index, day_branch_index)
        
        return {
            "is_kong_wang": day_branch_index in kong_wang_branches,
            "kong_wang_branches": kong_wang_branches,
            "is_jue_chu_feng_sheng": is_jue_chu_feng_sheng
        }
```

### 4. AI增强解读系统

**工业级提示词架构**：强制AI遵守物理引擎判定
```python
system_prompt = """你是一个极度严谨的周易术数推演引擎。
唯一目标：推演的绝对准确率与结果输出的稳定性。

接收到大六壬星盘数据后，你必须在后台进行生克穷举和逻辑自检。
确认逻辑闭环后，严格按照以下四个模板输出冷峻、精准的结论：

【定盘确真】：一句话点明当前局势的客观底层基调。
【核心推演链条】：用最精炼的大六壬专业术语展示核心生克逻辑。
【铁断与应期】：给出唯一的最终结论，并尝试推断精确到天干地支的应期。
【风控与应对】：若有破坏因素直接指出；若有转机，指出具体行为策略或方位。"""
```

## 🎯 技术特色

### 前端技术栈
- **Vue 3**：响应式组件架构
- **TypeScript**：类型安全的开发体验
- **Tauri**：跨平台桌面应用框架
- **CSS Grid/Flexbox**：现代化布局系统

### 后端技术栈
- **FastAPI**：高性能异步API框架
- **Pydantic**：数据验证和序列化
- **异步编程**：高效的并发处理
- **模块化设计**：清晰的系统架构

### 算法特色
- **五行生克算法**：标准的五行相生相克计算
- **天干地支映射**：完整的天文历法支持
- **路由决策树**：智能的多层降级策略
- **时空校准算法**：精确的天文时间计算

## 📊 性能表现

### 回测系统验证
项目包含完整的自动化回测系统，验证引擎的准确性和稳定性：

```bash
python backtest.py
```

**测试结果**：
- 100%引擎存活率
- 专业级推演准确性
- 稳定的API响应性能

## 🔮 应用场景

### 个人使用
- **命运推演**：事业、财运、感情等人生重大决策
- **时机选择**：重要活动的最佳时间窗口
- **风险预警**：潜在问题的提前识别和规避

### 专业应用
- **术数研究**：大六壬算法的现代化实现
- **AI集成**：传统智慧与人工智能的融合探索
- **教育工具**：古代术数的可视化教学

## 🤝 贡献指南

我们欢迎各种形式的贡献！请参考以下步骤：

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- **古代先贤**：传承千年的东方智慧
- **现代科技**：让古老术数焕发新生
- **开源社区**：无私的技术分享和支持

---

**大六壬赛博终端** - 让古老的智慧在数字时代绽放光芒 ✨