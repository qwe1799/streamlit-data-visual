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

# -------------------------- 障碍物持久化 --------------------------
OBSTACLE_FILE = "obstacles.json"

def load_obstacles():
    if os.path.exists(OBSTACLE_FILE):
        with open(OBSTACLE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_obstacles(obs_list):
    with open(OBSTACLE_FILE, 'w', encoding='utf-8') as f:
        json.dump(obs_list, f, ensure_ascii=False, indent=2)

# -------------------------- 初始化状态（核心：新增选取模式） --------------------------
if "select_mode" not in st.session_state:
    st.session_state.select_mode = False  # False: 未开启选取, True: 正在选取
if "current_points" not in st.session_state:
    st.session_state.current_points = []
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
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret

def _transform_lon(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret

# -------------------------- 地图渲染（核心：一键选取逻辑） --------------------------
def render_map(latA, lngA, latB, lngB, map_type):
    obstacles = load_obstacles()
    select_mode = st.session_state.select_mode
    points = st.session_state.current_points

    if map_type == "卫星影像地图":
        latA, lngA = gcj_to_wgs(latA, lngA)
        latB, lngB = gcj_to_wgs(latB, lngB)
        layer_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attribution = 'Tiles © Esri'
    else:
        layer_url = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
        attribution = '© 高德地图'

    points_json = json.dumps(points)

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

            // 绘制航线
            L.polyline([[{latA},{lngA}],[{latB},{lngB}]], {{color:'red', weight:5}}).addTo(map);
            L.marker([{latA},{lngA}]).addTo(map).bindPopup("起点A");
            L.marker([{latB},{lngB}]).addTo(map).bindPopup("终点B");

            // 绘制已保存障碍物
            const obstacles = {json.dumps(obstacles)};
            obstacles.forEach(obs => {{
                L.polygon(obs.points, {{
                    color: '#ff4444', fillColor: '#ff0000', fillOpacity: 0.3, weight:3
                }}).addTo(map).bindPopup(obs.name + " (" + obs.height + "m)");
            }});

            // 临时点数组
            var tempPoints = {points_json};
            var tempPoly = null;

            // 绘制临时多边形
            function drawTemp() {{
                if (tempPoly) map.removeLayer(tempPoly);
                if (tempPoints.length > 1) {{
                    tempPoly = L.polygon(tempPoints, {{color:'blue', fillOpacity:0.2}}).addTo(map);
                }}
            }}
            drawTemp();

            // 仅在选取模式下响应点击
            if ({select_mode}) {{
                map.on('click', function(e) {{
                    tempPoints.push([e.latlng.lat, e.latlng.lng]);
                    drawTemp();
                    window.Streamlit.setComponentValue(tempPoints);
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
        st.markdown("### 🚧 障碍物选取")
        
        # 核心：一键开启/结束选取
        if not st.session_state.select_mode:
            if st.button("🔴 开始选取障碍物", type="primary", use_container_width=True):
                st.session_state.select_mode = True
                st.session_state.current_points = []
                st.rerun()
        else:
            if st.button("✅ 结束选取并保存", type="primary", use_container_width=True):
                # 彻底删除打点限制，直接保存
                if len(st.session_state.current_points) >= 1:  # 仅需1个点即可保存（可改）
                    lst = load_obstacles()
                    lst.append({
                        "name": st.session_state.get("obs_name", "未命名"),
                        "height": st.session_state.get("obs_height", 25),
                        "points": st.session_state.current_points
                    })
                    save_obstacles(lst)
                    st.session_state.select_mode = False
                    st.session_state.current_points = []
                    st.success("✅ 障碍物保存成功！")
                    st.rerun()
                else:
                    st.warning("⚠️ 请至少点击1个点！")
            if st.button("❌ 取消选取", use_container_width=True):
                st.session_state.select_mode = False
                st.session_state.current_points = []
                st.rerun()
        
        # 高度和名称（仅在选取模式下显示）
        if st.session_state.select_mode:
            st.write(f"已打点：{len(st.session_state.current_points)}")
            obs_height = st.number_input("高度(m)", min_value=1, value=25, step=1, key="obs_height")
            obs_name = st.text_input("名称", value="教学楼", key="obs_name")
        
        # 清空当前打点（仅在选取模式下显示）
        if st.session_state.select_mode:
            if st.button("🗑️ 清空当前打点", use_container_width=True):
                st.session_state.current_points = []
                st.rerun()
        
        st.divider()
        st.markdown("### 📋 已保存障碍物")
        obs_list = load_obstacles()
        if obs_list:
            for i, obs in enumerate(obs_list):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"📍 {obs['name']} ({obs['height']}m)")
                with col2:
                    if st.button("删除", key=f"del_{i}", use_container_width=True):
                        del obs_list[i]
                        save_obstacles(obs_list)
                        st.rerun()
            if st.button("🧹 清空全部障碍物", use_container_width=True):
                save_obstacles([])
                st.rerun()
        else:
            st.info("暂无保存的障碍物")
            
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 右侧布局 --------------------------
with col_right:
    st.markdown("# 🎓 南京科技职业学院")
    st.markdown("## 无人机航线导航与监控系统")

    if page == "航线规划":
        map_switch = st.radio("🗺️ 地图模式", ["高德普通地图", "卫星影像地图"], horizontal=True)
        st.markdown("### ⛰️ 飞行高度设置")
        fly_height = st.number_input("飞行高度（米）", min_value=1, value=50, step=1)
        
        st.markdown("### 🎯 航线坐标")
        c1,c2 = st.columns(2)
        with c1:
            latA = st.number_input("起点A 纬度", value=32.2335, format="%.6f")
            lngA = st.number_input("起点A 经度", value=118.7475, format="%.6f")
        with c2:
            latB = st.number_input("终点B 纬度", value=32.2338, format="%.6f")
            lngB = st.number_input("终点B 经度", value=118.7479, format="%.6f")
        
        # 安全渲染地图
        try:
            map_res = components.html(render_map(latA, lngA, latB, lngB, map_switch), height=680)
            if isinstance(map_res, list) and st.session_state.select_mode:
                st.session_state.current_points = map_res
        except:
            pass

    else:
        st.title("📡 无人机心跳监控")
        c1,c2 = st.columns(2)
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
                    "序号": st.session_state.seq,
                    "时间": t,
                    "状态": "正常"
                })
                df = pd.DataFrame(st.session_state.heartbeat_data)
                with placeholder.container():
                    st.line_chart(df, x="时间", y="序号", color="状态")
                    st.dataframe(df, use_container_width=True)
                time.sleep(1)
