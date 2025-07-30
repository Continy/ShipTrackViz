document.addEventListener('DOMContentLoaded', function () {
    const viewer = new Cesium.Viewer('cesiumContainer', {
        terrain: Cesium.Terrain.fromWorldTerrain({
            requestVertexNormals: true,
            requestWaterMask: true,
        }),
        infoBox: false,
        selectionIndicator: true,
        shouldAnimate: true,
    });
    viewer.scene.globe.enableLighting = true;
    viewer.scene.globe.depthTestAgainstTerrain = true;
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
            // 7. 跟踪实体
            await trackEntity(viewer, entities);
            loadingOverlay.classList.add('hidden');

        } catch (error) {
            console.error('Initialization failed:', error);
            loadingOverlay.innerHTML = `<div class="loading-container"><div class="loading-title">Error</div><div>Could not load visualization data. Please check console.</div></div>`;
        }
    }
    async function trackEntity(viewer, entities) {
        try {
            const pointEntities = entities.filter(entity => entity.id.startsWith('point_'));
            if (pointEntities.length === 0) {
                console.warn('No point entities found for tracking');
                return;
            }

            // 获取时间范围
            console.log(`Tracking ${pointEntities.length} entities`);
            const firstEntity = pointEntities[0];
            const lastEntity = pointEntities[pointEntities.length - 1];

            const startTime = Cesium.JulianDate.fromIso8601(firstEntity.properties.timestamp_iso._value);
            const stopTime = Cesium.JulianDate.fromIso8601(lastEntity.properties.timestamp_iso._value);

            // 构建位置属性
            const trackPositionProperty = new Cesium.SampledPositionProperty();

            pointEntities.forEach(entity => {
                const time = Cesium.JulianDate.fromIso8601(entity.properties.timestamp_iso._value);
                const position = entity.position.getValue(time);
                if (position) {
                    trackPositionProperty.addSample(time, position);
                }
            });

            trackPositionProperty.setInterpolationOptions({
                interpolationDegree: 1,
                interpolationAlgorithm: Cesium.LagrangePolynomialApproximation
            });

            // 使用VelocityOrientationProperty，它会自动计算方向
            const orientationProperty = new Cesium.CallbackProperty(function (time, result) {
                // 先获取基础的VelocityOrientation
                const velocityOrientationProperty = new Cesium.VelocityOrientationProperty(trackPositionProperty);
                const baseOrientation = velocityOrientationProperty.getValue(time);

                if (!baseOrientation) return result;

                // 定义角度偏移（以弧度为单位）
                const headingOffset = Math.PI;    // 180度偏移 - 根据需要调整
                const pitchOffset = 0;            // 俯仰角偏移
                const rollOffset = 0;             // 滚转角偏移

                // 创建偏移的HeadingPitchRoll
                const offsetHPR = new Cesium.HeadingPitchRoll(headingOffset, pitchOffset, rollOffset);

                // 将偏移转换为四元数
                const offsetQuaternion = Cesium.Quaternion.fromHeadingPitchRoll(offsetHPR);

                // 应用偏移到基础方向
                return Cesium.Quaternion.multiply(baseOrientation, offsetQuaternion, result);
            }, false);
            // 尝试加载Ion资源
            let modelUri;
            try {
                modelUri = await Cesium.IonResource.fromAssetId(3588133);
                console.log('Ion model loaded successfully');
            } catch (ionError) {
                console.warn('Failed to load Ion model, using fallback:', ionError);
                modelUri = null;
            }

            // 创建船只实体
            const shipEntity = viewer.entities.add({
                availability: new Cesium.TimeIntervalCollection([
                    new Cesium.TimeInterval({
                        start: startTime,
                        stop: stopTime
                    })
                ]),
                name: "Tracked Ship",
                position: trackPositionProperty,
                orientation: orientationProperty,

                // 使用Ion模型或降级到基本几何体
                model: modelUri ? {
                    uri: modelUri,
                    minimumPixelSize: 64,
                    maximumScale: 20000,
                    scale: 100.0
                } : undefined,

                // 如果没有模型，使用几何体
                ellipsoid: !modelUri ? {
                    radii: new Cesium.Cartesian3(25.0, 10.0, 5.0),
                    material: Cesium.Color.BLUE.withAlpha(0.8),
                    outline: true,
                    outlineColor: Cesium.Color.WHITE
                } : undefined,

                path: {
                    width: 3,
                    material: new Cesium.PolylineGlowMaterialProperty({
                        glowPower: 0.2,
                        color: Cesium.Color.YELLOW
                    }),
                    leadTime: 0,
                    trailTime: 3600,
                    resolution: 120
                },

                label: {
                    text: 'Ship',
                    font: '12pt sans-serif',
                    pixelOffset: new Cesium.Cartesian2(0, -40),
                    fillColor: Cesium.Color.WHITE,
                    outlineColor: Cesium.Color.BLACK,
                    outlineWidth: 2,
                    style: Cesium.LabelStyle.FILL_AND_OUTLINE
                }
            });

            // 设置时钟和相机
            viewer.clock.startTime = startTime;
            viewer.clock.stopTime = stopTime;
            viewer.clock.currentTime = startTime;
            viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;
            viewer.clock.multiplier = 60;

            viewer.trackedEntity = shipEntity;

            // 初始相机位置
            const firstPosition = trackPositionProperty.getValue(startTime);
            if (firstPosition) {
                const cartographic = Cesium.Cartographic.fromCartesian(firstPosition);
                const longitude = Cesium.Math.toDegrees(cartographic.longitude);
                const latitude = Cesium.Math.toDegrees(cartographic.latitude);

                await viewer.camera.flyTo({
                    destination: Cesium.Cartesian3.fromDegrees(longitude, latitude, 5000),
                    orientation: {
                        heading: Cesium.Math.toRadians(0),
                        pitch: Cesium.Math.toRadians(-45),
                        roll: 0
                    },
                    duration: 3
                });
            }

            viewer.clock.shouldAnimate = true;
            console.log(`Ship tracking initialized with ${pointEntities.length} waypoints`);
            return shipEntity;

        } catch (error) {
            console.error('Error in trackEntity:', error);
            throw error;
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