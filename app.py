import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
import datetime
import json
import os
import math

# -------------------------- 配置 --------------------------
st.set_page_config(page_title="无人机系统", layout="wide")
st.markdown("""
<style>
.left-panel {background:#f8f9fa;padding:20px;border-radius:10px;height:95vh;}
</style>
""", unsafe_allow_html=True)

# -------------------------- 永久文件存储 --------------------------
OBSTACLE_FILE = "obstacles.json"

def load_obstacles():
    if os.path.exists(OBSTACLE_FILE):
        with open(OBSTACLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_obstacles(data):
    with open(OBSTACLE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------------- 状态初始化（绝对稳定） --------------------------
if "drawing" not in st.session_state:
    st.session_state.drawing = False

if "points" not in st.session_state:
    st.session_state.points = []

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

# -------------------------- 地图（极简稳定版） --------------------------
def render_map(latA, lngA, latB, lngB, map_type):
    obs = load_obstacles()
    drawing = st.session_state.drawing
    pts = st.session_state.points

    if map_type == "卫星影像地图":
        latA, lngA = gcj_to_wgs(latA, lngA)
        latB, lngB = gcj_to_wgs(latB, lngB)
        layer = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    else:
        layer = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"

    pts_json = json.dumps(pts)

    return f"""
    <html>
    <head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>#map {{width:100%;height:680px;}}</style>
    </head>
    <body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([32.2335,118.7475],17);
        L.tileLayer('{layer}',{{maxZoom:20}}).addTo(map);

        L.polyline([[{latA},{lngA}],[{latB},{lngB}]],{{color:'red',weight:4}}).addTo(map);
        L.marker([{latA},{lngA}]).bindPopup("起点").addTo(map);
        L.marker([{latB},{lngB}]).bindPopup("终点").addTo(map);

        const obs = {json.dumps(obs)};
        obs.forEach(o => {{
            L.polygon(o.points,{{color:'#f00',fillOpacity:0.3}}).bindPopup(o.name).addTo(map);
        }});

        var points = {pts_json};
        var poly = null;

        function redraw(){{
            if(poly) map.removeLayer(poly);
            if(points.length>=2) poly = L.polygon(points,{{color:'#00f',fillOpacity:0.2}}).addTo(map);
        }}
        redraw();

        if({str(drawing).lower()}){{
            map.on('click',function(e){{
                points.push([e.latlng.lat,e.latlng.lng]);
                redraw();
                window.Streamlit.setComponentValue(points);
            }});
        }}
    </script>
    </body>
    </html>
    """

# -------------------------- 界面 --------------------------
L, R = st.columns([1, 3])

with L:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)
    st.subheader("🧭 导航")
    page = st.radio("", ["航线规划", "飞行监控"], label_visibility="collapsed")
    st.divider()

    if page == "航线规划":
        st.markdown("### 🚧 障碍物圈选（记忆版）")
        h = st.number_input("高度(m)", 1, 500, 25)
        name = st.text_input("名称", "教学楼")

        # 稳定计数，绝对不报错
        st.info(f"当前已打点：{len(st.session_state.points)} 个")

        if not st.session_state.drawing:
            if st.button("🔴 开始圈选", type="primary", use_container_width=True):
                st.session_state.drawing = True
                st.rerun()
        else:
            if st.button("✅ 保存并结束", type="primary", use_container_width=True):
                if len(st.session_state.points) >= 3:
                    data = load_obstacles()
                    data.append({"name": name, "height": h, "points": st.session_state.points})
                    save_obstacles(data)
                    st.success("✅ 保存成功！永久显示！")
                st.session_state.points = []
                st.session_state.drawing = False
                st.rerun()

            if st.button("❌ 取消圈选（保留记忆）", use_container_width=True):
                st.session_state.drawing = False
                st.rerun()

        st.divider()
        st.markdown("### 📋 已保存障碍物")
        obs_list = load_obstacles()
        if not obs_list:
            st.info("暂无障碍物")
        else:
            for i, o in enumerate(obs_list):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"📍 {o['name']}")
                with c2:
                    if st.button("🗑️ 删", key=f"d{i}"):
                        del obs_list[i]
                        save_obstacles(obs_list)
                        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 右侧 --------------------------
with R:
    st.markdown("# 南京科技职业学院")
    st.markdown("## 无人机航线导航与监控系统")

    if page == "航线规划":
        t = st.radio("地图", ["高德普通地图", "卫星影像地图"], horizontal=True)
        c1, c2 = st.columns(2)
        with c1:
            latA = st.number_input("起点纬度", 32.2335, format="%.6f")
            lngA = st.number_input("起点经度", 118.7475, format="%.6f")
        with c2:
            latB = st.number_input("终点纬度", 32.2338, format="%.6f")
            lngB = st.number_input("终点经度", 118.7479, format="%.6f")

        res = components.html(render_map(latA, lngA, latB, lngB, t), height=680)
        if isinstance(res, list) and st.session_state.drawing:
            st.session_state.points = res

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
        while True:
            if st.session_state.running:
                st.session_state.seq += 1
                st.session_state.heartbeat_data.append({
                    "序号": st.session_state.seq,
                    "时间": datetime.datetime.now().strftime("%H:%M:%S"),
                    "状态": "正常"
                })
                df = pd.DataFrame(st.session_state.heartbeat_data)
                with placeholder.container():
                    st.line_chart(df, x="时间", y="序号")
                    st.dataframe(df)
                time.sleep(1)
            else:
                break
