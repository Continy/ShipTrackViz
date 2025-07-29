document.addEventListener('DOMContentLoaded', function () {
    const viewer = new Cesium.Viewer('cesiumContainer', {
        terrain: Cesium.Terrain.fromWorldTerrain(),
        infoBox: false,
        selectionIndicator: false,
        shouldAnimate: true,
    });
    viewer.scene.globe.enableLighting = true;

    const loadingOverlay = document.getElementById('loading-overlay');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const charts = [];

    async function initializeVisualization() {
        try {
            // 1. 从后端 API 获取数据，并跟踪进度
            const response = await fetch('/api/trajectory');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const contentLength = +response.headers.get('Content-Length');
            let receivedLength = 0;
            let chunks = [];

            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    break;
                }

                chunks.push(value);
                receivedLength += value.length;

                if (contentLength) {
                    const percent = Math.round((receivedLength / contentLength) * 100);
                    progressBar.style.width = percent + '%';
                    progressText.innerText = percent + '%';
                }
            }

            // 将所有接收到的数据块合并
            let chunksAll = new Uint8Array(receivedLength);
            let position = 0;
            for (let chunk of chunks) {
                chunksAll.set(chunk, position);
                position += chunk.length;
            }

            // 解码并解析 JSON
            const result = new TextDecoder("utf-8").decode(chunksAll);
            try {
                // 尝试解析 JSON
                data = JSON.parse(result);
            } catch (error) {
                // 如果解析失败，执行这里的代码
                console.error("!!! JSON Parsing Failed !!!");
                console.error("Error message:", error.message);
                console.log("--- Server Response (Raw Text) ---");

                // 将导致错误的原始字符串完整打印出来，这是最重要的调试信息
                console.log(result);

                // 更新 UI 告知用户错误
                loadingOverlay.innerHTML = `<div class="loading-container"><div class="loading-title">Error</div><div>Failed to parse server data. Please check the developer console (F12) for details.</div></div>`;

                // 抛出错误，终止后续代码执行
                throw new Error("Invalid JSON response from server.");
            }


            // --- 数据加载完成，开始设置可视化 ---
            progressText.innerText = 'Initializing...';

            // 2. 加载 CZML 数据到 Cesium
            const czmlDataSource = await Cesium.CzmlDataSource.load(data.czml);
            await viewer.dataSources.add(czmlDataSource);



            // 3. 设置点状图标
            const entities = czmlDataSource.entities.values;
            for (let i = 0; i < entities.length; i++) {
                const entity = entities[i];
                if (entity.id.startsWith('point_')) {
                    // 移除billboard，使用point
                    entity.billboard = undefined;
                    entity.point = new Cesium.PointGraphics({
                        pixelSize: 8,
                        color: Cesium.Color.ORANGERED,
                        outlineColor: Cesium.Color.WHITE,
                        outlineWidth: 2,
                        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
                    });
                }
            }



            // 4. 初始化 ECharts
            initializeECharts(data.echarts);

            // 5. 设置交互
            setupInteractions(viewer, data.echarts.timestamps);

            // 6. 等待 Cesium 场景渲染完成并缩放到轨迹
            await viewer.zoomTo(czmlDataSource);

            loadingOverlay.classList.add('hidden');

        } catch (error) {
            console.error('Initialization failed:', error);
            loadingOverlay.innerHTML = `<div class="loading-container"><div class="loading-title">Error</div><div>Could not load visualization data. Please check console.</div></div>`;
        }
    }

    function initializeECharts(echartsData) {
        const chartsContainer = document.getElementById('charts-container');
        echartsData.series.forEach(seriesData => {
            const chartDiv = document.createElement('div');
            chartDiv.className = 'chart-container';
            chartsContainer.appendChild(chartDiv);

            const chart = echarts.init(chartDiv, 'dark');
            const option = {
                title: { text: seriesData.title, left: 'center', textStyle: { fontSize: 14, color: '#eee' } },
                tooltip: { trigger: 'axis', backgroundColor: 'rgba(50,50,50,0.7)', borderColor: '#ccc', textStyle: { color: '#fff' } },
                xAxis: { type: 'category', data: echartsData.timestamps, axisLabel: { color: '#ccc' } },
                yAxis: { type: 'value', scale: true, axisLabel: { color: '#ccc' }, splitLine: { lineStyle: { color: '#444' } } },
                grid: { left: '20%', right: '8%', bottom: '25%' },
                series: [{ name: seriesData.title, data: seriesData.data, type: 'line', smooth: true, showSymbol: false }]
            };
            chart.setOption(option);
            charts.push(chart);
        });
    }

    function setupInteractions(viewer, timestamps) {
        viewer.selectedEntityChanged.addEventListener(function (selectedEntity) {
            if (Cesium.defined(selectedEntity) && Cesium.defined(selectedEntity.properties)) {
                const properties = selectedEntity.properties.getValue(viewer.clock.currentTime);

                let infoText = '';
                for (const [key, value] of Object.entries(properties)) {
                    let displayValue = value;
                    if (typeof value === 'number') displayValue = value.toFixed(4);
                    infoText += `${key.padEnd(15)}: ${displayValue}\n`;
                }
                document.getElementById('info-content').innerText = infoText;

                // 查找时间戳索引并更新图表
                const index = timestamps.findIndex(ts => new Date(ts).getTime() === new Date(properties.timestamp_iso).getTime());
                if (index > -1) {
                    updateCharts(timestamps[index]);
                }

            } else {
                document.getElementById('info-content').innerText = "Click on a point to see details";
                clearChartMarkers();
            }
        });
    }

    function updateCharts(timestamp) {
        const markLineOpt = {
            silent: true, symbol: 'none',
            lineStyle: { type: 'dashed', color: '#00BFFF' },
            data: [{ xAxis: timestamp }]
        };
        charts.forEach(chart => chart.setOption({ series: [{ markLine: markLineOpt }] }));
    }

    function clearChartMarkers() {
        charts.forEach(chart => chart.setOption({ series: [{ markLine: { data: [] } }] }));
    }

    initializeVisualization();
});