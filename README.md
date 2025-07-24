# ShipTrackViz

## 概述 (Overview)

ShipTrackViz 是一个用于可视化航运数据的强大工具，旨在提供对航运模式、延误和整体效率的深入洞察。

## 功能特性 (Features)

- [ ] 可视化航线交互式地图
  - [ ] 为不同航线提供地图图层
  - [ ] 可定制的船舶标记
- [ ] 性能指标的动态图表
- [ ] 高效处理大规模数据集
- [ ] 更多功能正在规划中！

## 技术栈 (Tech Stack)

- **后端 (数据处理)**: Python
  - 使用 Pandas, NumPy, 和 Xarray 进行数据清洗、处理和分析。
- **前端 (数据可视化)**: JavaScript
  - 使用 Leaflet.js 创建交互式地图。
  - 使用 ECharts.js 生成动态和可定制的图表。

## 项目结构 (Project Structure)

```
.
├── backend/              # Python 后端代码 (数据处理 API)
│   ├── data_processing/
│   └── main.py
├── frontend/             # JavaScript 前端代码 (UI 和可视化)
│   ├── css/
│   ├── js/
│   └── index.html
├── data/                 # 原始和处理后的数据集
│   ├── raw/
│   └── processed/
└── README.md
```

## 环境与依赖 (Prerequisites & Dependencies)

### 后端

- Python 3.11+
- Pip (Python 包管理器)
- **Python 库**:
  - `pandas`
  - `numpy`
  - `xarray`
  - `matplotlib`

### 前端

- **JavaScript 库**:
  - `Leaflet.js`
  - `Echarts.js`

## 快速开始 (Getting Started)

1. **克隆仓库**

    ```bash
    git clone https://github.com/Continy/ShipTrackViz.git
    cd ShipTrackViz
    ```

2. **设置后端**

    ```bash
    # 创建并激活虚拟环境
    conda create -n shiptrackviz python=3.11
    conda activate shiptrackviz
    # 安装后端依赖
    pip install -r requirements.txt

    ```

3. **运行前端**
    - 在浏览器中直接打开 `frontend/index.html` 文件，或使用一个简单的本地服务器。
