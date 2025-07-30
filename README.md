# ShipTrackViz

## 概述 (Overview)

ShipTrackViz 是一个船舶轨迹可视化工具，基于现代Web技术栈构建，提供交互式3D轨迹可视化、实时数据分析和多维环境数据集成。该工具专为海事研究、航运分析和轨迹数据可视化而设计。

## 功能特性 (Features)

- [x] **3D交互式轨迹可视化**
  - [x] 基于 CesiumJS 的全球3D地球渲染
  - [x] 实时船舶模型跟踪和动画
  - [x] 可定制的轨迹路径和点标记

- [x] **智能数据处理**
  - [x] 支持 CSV/Excel 文件自动解析
  - [x] LLM驱动的表头识别和数据结构分析
  - [x] 自动时间序列插值和数据清洗
  - [x] 缓存机制优化大数据集处理

- [x] **多维数据分析**
  - [x] ECharts集成的动态图表系统
  - [x] 实时环境数据（风速、风向）集成
  - [x] GRIB格式气象数据支持
  - [x] 轨迹点属性交互式查看

- [x] **环境数据集成**
  - [x] NetCDF/GRIB格式气象数据读取
  - [x] 多层风场数据（10m/100m高度）
  - [x] 时空插值匹配轨迹数据

## 技术栈 (Tech Stack)

### 后端 (Backend)

- **Python 3.11+**
- **数据处理**: Pandas, NumPy, Xarray
- **Web框架**: Flask
- **地理数据**: GRIB, NetCDF
- **AI集成**: Google Generative AI (Gemini)

### 前端 (Frontend)

- **3D可视化**: CesiumJS 1.131
- **图表**: ECharts 5.3.3
- **数据格式**: CZML, JSON
- **UI交互**: 原生JavaScript + CSS

### 数据格式支持

- **轨迹数据**: CSV, Excel (XLSX)
- **气象数据**: GRIB, NetCDF
- **可视化**: CZML, GeoJSON

## 项目结构 (Project Structure)

```
ShipTrackViz/
├── app.py                    # Flask Web应用主入口
├── main.py                   # 项目运行脚本
├── requirements.txt          # Python依赖包
├── .env                      # 环境变量配置
│
├── track/                    # 轨迹处理核心模块
│   ├── trackloader.py        # 数据加载和解析
│   ├── traj.py              # 轨迹对象和可视化容器
│   └── point.py             # 轨迹点数据结构
│
├── utils/                    # 工具函数
│   ├── cfg.py               # 配置管理
│   ├── geo.py               # 地理计算工具
│   └── llmengine.py         # LLM集成引擎
│
├── static/                   # 前端静态资源
│   ├── js/
│   │   ├── main.js          # 主要前端逻辑
│   │   └── env.js           # 环境配置
│   └── css/
│       └── style.css        # 样式文件
│
├── templates/                # HTML模板
│   └── index.html           # 主页面模板
│
├── llm/                     # LLM配置
│   └── data.yaml            # 数据解析提示配置
│
└── data/                    # 数据目录
    ├── *.csv                # 轨迹数据文件
    ├── *.grib               # 气象数据文件
    └── cache/               # 数据缓存目录
```

## 环境与依赖 (Prerequisites & Dependencies)

### 系统要求

- Python 3.11+
- 现代Web浏览器（支持WebGL）
- 4GB+ RAM（推荐用于大数据集）

### Python依赖

```bash
# 数据处理
pandas>=1.5.0
numpy>=1.24.0
xarray>=2023.1.0

# Web框架
flask>=2.3.0

# 地理数据处理
cfgrib>=0.9.10
netcdf4>=1.6.0

# AI集成
google-generativeai>=0.3.0

# 配置管理
yacs>=0.1.8
python-dotenv>=1.0.0

# UI增强
tqdm>=4.65.0
rich>=13.0.0
```

### 前端依赖（CDN引入）

- CesiumJS 1.131
- ECharts 5.3.3

## 快速开始 (Getting Started)

### 1. 环境配置

```bash
# 克隆仓库
git clone https://github.com/Continy/ShipTrackViz.git
cd ShipTrackViz

# 创建虚拟环境
conda create -n shiptrackviz python=3.11
conda activate shiptrackviz

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# Cesium访问令牌（从 https://cesium.com/ion/tokens 获取）
CESIUM_ACCESS_TOKEN=your_cesium_token_here

# Google AI API密钥（可选，用于智能数据解析）
GOOGLE_API_KEY=your_google_api_key_here
```

### 3. 准备数据

将轨迹数据文件放置在 `data/` 目录：

```
data/
├── your_trajectory.csv      # 包含 lat, lon, timestamp 列
└── weather_data.grib        # 气象数据（可选）
```

### 4. 运行应用

```python
# 修改 main.py 中的数据路径
path = Path('./data/your_trajectory.csv').resolve()

# 运行可视化
python main.py
```

### 5. 访问应用

打开浏览器访问：`http://localhost:8000`

## 使用指南 (Usage Guide)

### 基本轨迹可视化

```python
from track.trackloader import DataChunk
from track.traj import Trajectory, TrajVizContainer

# 加载数据
chunk = DataChunk(
    path='./data/ship_track.csv',
    cfg='./llm/data.yaml',
    encode='utf-8'
)

# 创建轨迹对象
traj = Trajectory(Datachunk=chunk)

# 启动Web可视化
visualizer = TrajVizContainer(traj, engine='webgl')
visualizer.launch_web_app(port=8000, debug=False)
```

### 集成环境数据

```python
# 添加风场数据
traj.setwinddata('./data/weather.grib', engine='cfgrib')

# 获取风速风向数据
wind_speed_10m = traj['w10']
wind_direction_10m = traj['w10_angle']
```

### 数据清洗和过滤

```python
from functools import partial

def valid_range_filter(data, range=(0, 1000)):
    return np.where((data < range[0]) | (data > range[1]), np.nan, data)

# 应用数据过滤器
chunk = DataChunk(
    path='./data/ship_track.csv',
    cfg='./llm/data.yaml',
    clip={
        'fuel_consumption': partial(valid_range_filter, range=(0, 500)),
        'speed': partial(valid_range_filter, range=(0, 30))
    }
)
```

## API文档 (API Documentation)

### 主要接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 主可视化页面 |
| `/api/trajectory` | GET | 获取轨迹数据（CZML + ECharts格式） |

### 数据格式

#### 轨迹数据输入

```csv
timestamp,latitude,longitude,speed,fuel_consumption
2024-01-01 00:00:00,23.1291,113.2644,12.5,45.2
2024-01-01 01:00:00,23.1355,113.2701,13.1,46.8
```

#### API输出格式

```json
{
    "czml": [...],           // 3D可视化数据
    "echarts": {
        "timestamps": [...], // 时间序列
        "series": [...]      // 图表数据系列
    }
}
```

## 其他功能 (Additional Features)

### 1. 智能数据解析

- 基于LLM的CSV/Excel表头自动识别
- 多语言表头支持（中文/英文）
- 数据类型自动推断

### 2. 实时3D跟踪

- 船舶模型实时动画
- 轨迹路径动态显示
- 相机智能跟踪

### 3. 多维数据分析

- 时间序列图表联动
- 轨迹点属性交互查看
- 环境数据叠加分析

### 4. 性能优化

- 大数据集分块处理
- 智能缓存机制
- 渐进式数据加载

## 故障排除 (Troubleshooting)

### 常见问题

**Q: Cesium渲染错误**

```terminal
Error: Cannot read properties of undefined (reading 'getValueInReferenceFrame')
```

A: 检查轨迹数据完整性，确保时间戳格式正确

**Q: 端口占用错误**

```terminal
OSError: [Errno 48] Address already in use
```

A: 更改端口或杀死占用进程：`lsof -ti:8000 | xargs kill -9`

**Q: 数据加载缓慢**

A: 启用数据缓存和分块处理，减少数据集大小

## 贡献指南 (Contributing)

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/new-feature`)
3. 提交更改 (`git commit -am 'Add new feature'`)
4. 推送到分支 (`git push origin feature/new-feature`)
5. 创建Pull Request

## 许可证 (License)

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---
