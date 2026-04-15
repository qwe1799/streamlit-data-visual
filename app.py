import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
import datetime
import math
import json
import os

# -------------------------- 页面配置 --------------------------
st.set_page_config(
    page_title="南京科技职业学院 - 无人机导航系统",
    layout="wide"
)

# -------------------------- 样式 --------------------------
st.markdown("""
<style>
.left-panel {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    height: 95vh;
}
</style>
""", unsafe_allow_html=True)

# -------------------------- 障碍物持久化（核心：JSON永久存储） --------------------------
OBSTACLE_FILE = "obstacles.json"

def load_obstacles():
    """从JSON加载所有障碍物，关闭页面再打开依然存在"""
    if os.path.exists(OBSTACLE_FILE):
        with open(OBSTACLE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_obstacles(obs_list):
    """保存障碍物到JSON文件，永久存储"""
    with open(OBSTACLE_FILE, 'w', encoding='utf-8') as f:
        json.dump(obs_list, f, ensure_ascii=False, indent=2)

# -------------------------- 初始化状态（核心：状态管理） --------------------------
if "drawing" not in st.session_state:
    st.session_state.drawing = False  # False: 未绘制, True: 正在绘制
if "current_points" not in st.session_state:
    st.session_state.current_points = []  # 存储当前绘制的点
if "heartbeat_data" not in st.session_state:
    st.session_state.heartbeat_data = []
    st.session_state.seq = 0
    st.session_state.running = False

# -------------------------- 坐标转换 --------------------------
def gcj_to_wgs(lat, lon):
    a = 6378245.0
    ee = 0.006693421622965943
    dlat = _transform_lat(lon - 105.0, lat - 35.0)
    dlon = _transform_lon(lon - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
    dlon = (dlon * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
    return lat - dlat, lon - dlon

def _transform_lat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    return ret

def _transform_lon(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    return ret

# -------------------------- 地图渲染（核心：状态同步） --------------------------
def render_map(latA, lngA, latB, lngB, map_type):
    obstacles = load_obstacles()
    drawing = st.session_state.drawing
    points = st.session_state.current_points  # 从session_state加载当前点

    if map_type == "卫星影像地图":
        latA, lngA = gcj_to_wgs(latA, lngA)
        latB, lngB = gcj_to_wgs(latB, lngB)
        layer = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attr = "Esri"
    else:
        layer = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
        attr = "© 高德"

    # 序列化当前点，前端初始化时加载
    points_json = json.dumps(points)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>#map {{width:100%;height:680px;border-radius:8px;}}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([32.2335, 118.7475], 17);
            L.tileLayer('{layer}', {{maxZoom:20, attribution:'{attr}'}}).addTo(map);

            // 绘制航线
            L.polyline([[{latA},{lngA}],[{latB},{lngB}]], {{color:'red',weight:4}}).addTo(map);
            L.marker([{latA},{lngA}]).bindPopup("起点").addTo(map);
            L.marker([{latB},{lngB}]).bindPopup("终点").addTo(map);

            // 绘制已保存的障碍物（红色半透明，永久显示）
            const obs = {json.dumps(obstacles)};
            obs.forEach(o => {{
                L.polygon(o.points, {{color:'#f00',fillColor:'#f44',fillOpacity:0.3}})
                 .bindPopup(o.name + " " + o.height + "m").addTo(map);
            }});

            // 初始化临时点数组（从后端session_state加载）
            var points = {points_json};
            var poly = null;

            // 绘制临时多边形（蓝色半透明）
            function redraw() {{
                if (poly) map.removeLayer(poly);
                if (points.length >= 2) {{
                    poly = L.polygon(points, {{color:'#00f',fillOpacity:0.2}}).addTo(map);
                }}
            }}
            redraw();

            // 仅在绘制模式下响应点击
            if ({str(drawing).lower()}) {{
                map.on('click', function(e) {{
                    points.push([e.latlng.lat, e.latlng.lng]);
                    redraw();
                    // 每次点击都回传点集，更新session_state
                    window.Streamlit.setComponentValue(points);
                }});
            }}
        </script>
    </body>
    </html>
    """
    return html

# -------------------------- 左侧布局 --------------------------
col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)
    st.subheader("🧭 导航")
    page = st.radio("", ["航线规划", "飞行监控"], label_visibility="collapsed")
    st.divider()

    if page == "航线规划":
        st.markdown("### 🚧 障碍物圈选")

        # 高度和名称输入
        height = st.number_input("高度(m)", min_value=1, max_value=500, value=25, step=1)
        name = st.text_input("名称", value="教学楼")

        # 绘制控制按钮
        if not st.session_state.drawing:
            if st.button("🔴 开始圈选障碍物", type="primary", use_container_width=True):
                st.session_state.drawing = True
                st.session_state.current_points = []  # 清空历史点
                st.rerun()
        else:
            if st.button("✅ 保存并结束圈选", type="primary", use_container_width=True):
                # 核心：保存前先获取最新点集，再写入JSON
                if len(st.session_state.current_points) > 0:
                    all_obs = load_obstacles()
                    all_obs.append({
                        "name": name,
                        "height": height,
                        "points": st.session_state.current_points
                    })
                    save_obstacles(all_obs)
                    st.success("✅ 障碍物已永久保存！")
                # 结束绘制，清空临时点
                st.session_state.drawing = False
                st.session_state.current_points = []
                st.rerun()

            if st.button("❌ 取消圈选", use_container_width=True):
                st.session_state.drawing = False
                st.session_state.current_points = []
                st.rerun()

        st.divider()
        st.markdown("### 📋 已保存障碍物")
        obs_list = load_obstacles()
        if obs_list:
            for i, o in enumerate(obs_list):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"📍 {o['name']} ({o['height']}m)")
                with c2:
                    if st.button("🗑️ 删除", key=f"del_{i}", use_container_width=True):
                        del obs_list[i]
                        save_obstacles(obs_list)
                        st.rerun()
            if st.button("🧹 清空全部障碍物", use_container_width=True):
                save_obstacles([])
                st.rerun()
        else:
            st.info("暂无障碍物")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 右侧布局 --------------------------
with col_right:
    st.markdown("# 🎓 南京科技职业学院")
    st.markdown("## 无人机航线导航与监控系统")

    if page == "航线规划":
        map_type = st.radio("🗺️ 地图模式", ["高德普通地图", "卫星影像地图"], horizontal=True)
        st.markdown("### ⛰️ 飞行高度设置")
        fly_h = st.number_input("飞行高度(m)", min_value=1, max_value=500, value=50, step=1)

        st.markdown("### 🎯 航线坐标")
        c1, c2 = st.columns(2)
        with c1:
            latA = st.number_input("起点纬度", value=32.2335, format="%.6f")
            lngA = st.number_input("起点经度", value=118.7475, format="%.6f")
        with c2:
            latB = st.number_input("终点纬度", value=32.2338, format="%.6f")
            lngB = st.number_input("终点经度", value=118.7479, format="%.6f")

        # 渲染地图，同步点集到session_state
        map_res = components.html(render_map(latA, lngA, latB, lngB, map_type), height=680)
        # 安全更新session_state
        if isinstance(map_res, list) and st.session_state.drawing:
            st.session_state.current_points = map_res

    else:
        st.title("📡 无人机心跳监控")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶️ 开始监测"):
                st.session_state.running = True
        with c2:
            if st.button("⏸️ 暂停监测"):
                st.session_state.running = False

        placeholder = st.empty()
        if st.session_state.running:
            while st.session_state.running:
                st.session_state.seq += 1
                t = datetime.datetime.now().strftime("%H:%M:%S")
                st.session_state.heartbeat_data.append({
                    "序号": st.session_state.seq, "时间": t, "状态": "正常"
                })
                df = pd.DataFrame(st.session_state.heartbeat_data)
                with placeholder.container():
                    st.line_chart(df, x="时间", y="序号", color="状态")
                    st.dataframe(df, use_container_width=True)
                time.sleep(1)
