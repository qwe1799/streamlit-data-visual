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
    padding: 25px;
    border-radius: 10px;
    height: 100vh;
}
/* 禁用地图点击样式 */
.leaflet-container {
    cursor: default !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------- 障碍物文件存储 --------------------------
OBSTACLE_FILE = "obstacles.json"

def load_obstacles():
    if os.path.exists(OBSTACLE_FILE):
        with open(OBSTACLE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_obstacles(obs_list):
    with open(OBSTACLE_FILE, 'w', encoding='utf-8') as f:
        json.dump(obs_list, f, ensure_ascii=False, indent=2)

def add_obstacle(name, points):
    data = load_obstacles()
    data.append({"name": name, "points": points})
    save_obstacles(data)

def delete_obstacle(idx):
    data = load_obstacles()
    if 0 <= idx < len(data):
        del data[idx]
        save_obstacles(data)

# -------------------------- 初始化session状态 --------------------------
if "draw_mode" not in st.session_state:
    st.session_state.draw_mode = False  # 是否开启选取模式
if "current_polygon" not in st.session_state:
    st.session_state.current_polygon = []  # 当前正在绘制的点
if "heartbeat_data" not in st.session_state:
    st.session_state.heartbeat_data = []
    st.session_state.seq = 0
    st.session_state.last_receive_time = time.time()
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
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret

def _transform_lon(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret

# -------------------------- 地图渲染（核心改进） --------------------------
def render_map(latA_gcj, lngA_gcj, latB_gcj, lngB_gcj, map_type, height):
    obstacles = load_obstacles()
    draw_mode = st.session_state.get("draw_mode", False)
    
    if map_type == "卫星影像地图":
        latA, lngA = gcj_to_wgs(latA_gcj, lngA_gcj)
        latB, lngB = gcj_to_wgs(latB_gcj, lngB_gcj)
        layer_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attribution = 'Tiles © Esri'
    else:
        latA, lngA = latA_gcj, lngA_gcj
        latB, lngB = latB_gcj, lngB_gcj
        layer_url = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
        attribution = '© 高德地图'

    # 构建HTML模板，根据draw_mode决定是否绑定点击事件
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            #map {{width:100%;height:650px;border-radius:10px;}}
            .leaflet-interactive {{ cursor: {(draw_mode and 'crosshair' or 'default')} !important; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([32.2335, 118.7475], 17);
            L.tileLayer('{layer_url}', {{maxZoom:20,attribution:'{attribution}'}}).addTo(map);

            // 绘制已保存的障碍物
            const obstacles = {obstacles};
            obstacles.forEach((obs, idx) => {{
                L.polygon(obs.points, {{
                    color: '#ff4444',
                    fillColor: '#ff0000',
                    fillOpacity: 0.3,
                    weight: 3
                }}).addTo(map).bindPopup(`障碍物：${obs.name}`);
            }});

            // 绘制临时多边形（当前正在绘制的）
            var tempPoints = [];
            var tempPolygon = null;

            // 只有开启选取模式才响应点击
            if ({draw_mode}) {{
                map.on('click', function(e) {{
                    const lat = e.latlng.lat;
                    const lng = e.latlng.lng;
                    tempPoints.push([lat, lng]);
                    
                    if (tempPolygon) map.removeLayer(tempPolygon);
                    if (tempPoints.length > 1) {{
                        tempPolygon = L.polygon(tempPoints, {{
                            color:'blue', 
                            fillOpacity:0.2,
                            weight: 2
                        }}).addTo(map);
                    }}
                }});
            }}

            // 暴露函数给Python获取数据
            window.getDrawState = function() {{
                return {{
                    isDrawing: tempPoints.length >= 3,
                    points: tempPoints
                }};
            }};
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
    st.subheader("📊 状态")
    st.success("✅ 系统正常")
    if st.session_state.get("draw_mode", False):
        st.info("🔴 已开启选取模式")
    else:
        st.warning("⚪ 未开启选取模式")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 右侧内容 --------------------------
with col_right:
    st.markdown("# 🎓 南京科技职业学院")
    st.markdown("## 无人机航线导航与监控系统")

    if page == "航线规划":
        # --- 地图切换 ---
        map_switch = st.radio("🗺️ 地图模式", ["高德普通地图", "卫星影像地图"], horizontal=True)
        
        # --- 飞行高度 ---
        st.markdown("### ⛰️ 飞行高度设置")
        fly_height = st.number_input("飞行高度（米）", min_value=1, value=50, step=1, key="fly_height")
        
        st.markdown("---")
        st.markdown("### 🎯 航线坐标")
        colA1, colA2 = st.columns(2)
        with colA1:
            latA = st.number_input("起点A 纬度", value=32.2335, format="%.6f", key="latA")
        with colA2:
            lngA = st.number_input("起点A 经度", value=118.7475, format="%.6f", key="lngA")

        colB1, colB2 = st.columns(2)
        with colB1:
            latB = st.number_input("终点B 纬度", value=32.2338, format="%.6f", key="latB")
        with colB2:
            lngB = st.number_input("终点B 经度", value=118.7479, format="%.6f", key="lngB")

        st.markdown("---")
        st.markdown("### 🚧 障碍物选取与绘制")
        
        # --- 核心操作区：开启选取 + 保存 ---
        col1, col2 = st.columns(2)
        with col1:
            # 开启选取按钮
            if st.button("🔴 开启选取模式", type="primary", use_container_width=True):
                st.session_state.draw_mode = True
                st.session_state.current_polygon = []  # 重置绘制点
                st.rerun()  # 强制刷新地图样式
        
        with col2:
            # 保存按钮（仅在开启模式且绘制有效时可用）
            draw_state = components.html(
                render_map(latA, lngA, latB, lngB, map_switch, fly_height), 
                height=670
            )
            # 安全获取前端绘制状态
            current_draw_state = st.session_state.get("current_draw_state", {"isDrawing": False})
            
            if st.button("✅ 保存当前障碍物", 
                         disabled=not st.session_state.get("draw_mode", False) or not current_draw_state["isDrawing"],
                         use_container_width=True):
                # 获取绘制点并保存
                obs_points = current_draw_state["points"]
                if obs_points:
                    add_obstacle(st.session_state.get("obs_name", "未命名障碍物"), obs_points)
                    # 保存后重置状态
                    st.session_state.draw_mode = False
                    st.session_state.current_polygon = []
                    st.success("✅ 障碍物保存成功！")
                    time.sleep(0.5)
                    st.rerun()

        # --- 障碍物管理区 ---
        st.markdown("#### 📋 已保存障碍物列表")
        obs_list = load_obstacles()
        
        if not obs_list:
            st.info("暂无保存的障碍物")
        else:
            # 显示所有障碍物，带删除按钮
            for i, obs in enumerate(obs_list):
                cols_show = st.columns([4, 1])
                with cols_show[0]:
                    st.write(f"📍 {obs['name']}")
                with cols_show[1]:
                    if st.button("🗑️ 删除", key=f"del_obs_{i}"):
                        delete_obstacle(i)
                        st.rerun()

        # --- 隐藏输入框（名称由前端或默认提供） ---
        obs_name = st.text_input("障碍物名称（选填）", placeholder="例如：教学楼A栋", key="obs_name")

    # -------------------------- 心跳监控 --------------------------
    else:
        st.title("📡 无人机通信心跳监测")
        col_start, col_stop = st.columns(2)
        with col_start:
            if st.button("▶️ 开始监测"):
                st.session_state.running = True
        with col_stop:
            if st.button("⏸️ 暂停监测"):
                st.session_state.running = False

        def simulate_heartbeat():
            st.session_state.seq += 1
            t = datetime.datetime.now().strftime("%H:%M:%S")
            st.session_state.last_receive_time = time.time()
            st.session_state.heartbeat_data.append({
                "序号": st.session_state.seq, "时间": t, "状态": "正常"
            })

        placeholder = st.empty()
        if st.session_state.get("running", False):
            while st.session_state.running:
                simulate_heartbeat()
                df = pd.DataFrame(st.session_state.heartbeat_data)
                with placeholder.container():
                    st.line_chart(df, x="时间", y="序号", color="状态", height=300)
                    st.dataframe(df, use_container_width=True, height=300)
                time.sleep(1)
