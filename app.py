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

def delete_obstacle(index):
    data = load_obstacles()
    if 0 <= index < len(data):
        del data[index]
        save_obstacles(data)

# -------------------------- 初始化session状态 --------------------------
if "draw_mode" not in st.session_state:
    st.session_state.draw_mode = False
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

# -------------------------- 地图渲染（已修复JS错误） --------------------------
def render_map(latA_gcj, lngA_gcj, latB_gcj, lngB_gcj, map_type):
    obstacles = load_obstacles()
    draw_mode = st.session_state.draw_mode

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

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>#map {{width:100%;height:680px;border-radius:10px;}}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([32.2335, 118.7475], 17);
            L.tileLayer('{layer_url}', {{maxZoom:20,attribution:'{attribution}'}}).addTo(map);

            const obstacles = {obstacles};
            obstacles.forEach((obs, idx) => {{
                L.polygon(obs.points, {{
                    color: '#ff4444', fillColor: '#ff0000', fillOpacity: 0.3, weight: 3
                }}).addTo(map).bindPopup("障碍物：" + obs.name);
            }});

            var tempPoints = [];
            var tempPoly = null;
            if ({draw_mode}) {{
                map.on('click', function(e) {{
                    tempPoints.push([e.latlng.lat, e.latlng.lng]);
                    if (tempPoly) map.removeLayer(tempPoly);
                    if (tempPoints.length >= 3) {{
                        tempPoly = L.polygon(tempPoints, {{color:'blue', fillOpacity:0.2}}).addTo(map);
                    }}
                }});
            }}

            window.Streamlit.setComponentValue({{
                points: tempPoints,
                is_valid: tempPoints.length >= 3
            }});
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
    if st.session_state.draw_mode:
        st.info("🔴 已开启障碍物选取模式")
    else:
        st.warning("⚪ 未开启选取，地图只读")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 右侧内容 --------------------------
with col_right:
    st.markdown("# 🎓 南京科技职业学院")
    st.markdown("## 无人机航线导航与监控系统")

    if page == "航线规划":
        map_switch = st.radio("🗺️ 地图模式", ["高德普通地图", "卫星影像地图"], horizontal=True)
        
        st.markdown("### ⛰️ 飞行高度设置")
        fly_height = st.number_input("飞行高度（米）", min_value=1, value=50, step=1)
        
        st.markdown("---")
        st.markdown("### 🎯 航线坐标")
        colA1, colA2 = st.columns(2)
        with colA1:
            latA = st.number_input("起点A 纬度", value=32.2335, format="%.6f")
        with colA2:
            lngA = st.number_input("起点A 经度", value=118.7475, format="%.6f")

        colB1, colB2 = st.columns(2)
        with colB1:
            latB = st.number_input("终点B 纬度", value=32.2338, format="%.6f")
        with colB2:
            lngB = st.number_input("终点B 经度", value=118.7479, format="%.6f")

        st.markdown("---")
        st.markdown("### 🚧 障碍物管理")
        
        col_draw, col_save = st.columns(2)
        with col_draw:
            if st.button("🔴 开启障碍物选取", type="primary", use_container_width=True):
                st.session_state.draw_mode = True
                st.rerun()
        with col_save:
            map_data = components.html(render_map(latA, lngA, latB, lngB, map_switch), height=700)
            obs_name = st.text_input("障碍物名称", placeholder="如：教学楼、塔吊")
            save_disabled = not st.session_state.draw_mode or not (map_data and map_data.get("is_valid", False))
            if st.button("✅ 保存当前障碍物", disabled=save_disabled, use_container_width=True):
                if map_data and map_data.get("points"):
                    add_obstacle(obs_name or "未命名障碍物", map_data["points"])
                    st.session_state.draw_mode = False
                    st.success("✅ 障碍物保存成功！")
                    st.rerun()

        # 已保存障碍物 + 删除功能
        st.markdown("#### 📋 已保存障碍物")
        obs_list = load_obstacles()
        if not obs_list:
            st.info("暂无保存的障碍物")
        else:
            for idx, obs in enumerate(obs_list):
                col_n, col_d = st.columns([4,1])
                with col_n:
                    st.write(f"📍 {obs['name']}")
                with col_d:
                    if st.button("🗑️ 删除", key=f"del_{idx}", use_container_width=True):
                        delete_obstacle(idx)
                        st.rerun()

    # -------------------------- 飞行监控 --------------------------
    else:
        st.title("📡 无人机通信心跳监测")
        col_start, col_stop = st.columns(2)
        with col_start:
            if st.button("▶️ 开始监测"):
                st.session_state.running = True
        with col_stop:
            if st.button("⏸️ 暂停监测"):
                st.session_state.running = False

        placeholder = st.empty()
        if st.session_state.get("running", False):
            while st.session_state.running:
                st.session_state.seq += 1
                t = datetime.datetime.now().strftime("%H:%M:%S")
                st.session_state.heartbeat_data.append({
                    "序号": st.session_state.seq, "时间": t, "状态": "正常"
                })
                df = pd.DataFrame(st.session_state.heartbeat_data)
                with placeholder.container():
                    st.line_chart(df, x="时间", y="序号", color="状态", height=300)
                    st.dataframe(df, use_container_width=True, height=300)
                time.sleep(1)
