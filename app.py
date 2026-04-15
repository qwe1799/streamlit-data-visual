import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
import datetime
import math

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

# -------------------------- 坐标转换（解决偏移） --------------------------
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

# -------------------------- 地图（高德+卫星） --------------------------
def render_map(latA_gcj, lngA_gcj, latB_gcj, lngB_gcj, map_type):
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

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>#map {width:100%;height:680px;border-radius:10px;}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([32.2335, 118.7475], 17);
            L.tileLayer('""" + layer_url + """', {maxZoom:20,attribution:'""" + attribution + """'}).addTo(map);
            L.marker([""" + str(latA) + """, """ + str(lngA) + """]).addTo(map).bindPopup("起点A");
            L.marker([""" + str(latB) + """, """ + str(lngB) + """]).addTo(map).bindPopup("终点B");
            L.polyline([[""" + str(latA) + """,""" + str(lngA) + """],[""" + str(latB) + """,""" + str(lngB) + """]],{color:'red',weight:5}).addTo(map);
        </script>
    </body>
    </html>
    """
    return html

# -------------------------- 左侧面板 --------------------------
col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)
    st.subheader("🧭 导航")
    page = st.radio("", ["航线规划", "飞行监控"], index=0, label_visibility="collapsed")
    st.divider()
    st.subheader("⚙️ 坐标系设置")
    coord_type = st.radio("", ["WGS-84", "GCJ-02(高德/百度)"], index=1, label_visibility="collapsed")
    st.divider()
    st.subheader("📊 系统状态")
    st.success("✅ A点已设")
    st.success("✅ B点已设")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 右侧 --------------------------
with col_right:
    st.markdown("# 🎓 南京科技职业学院")
    st.markdown("### 无人机航线导航与监控系统")

    if page == "航线规划":
        map_switch = st.radio("🗺️ 地图模式", ["高德普通地图", "卫星影像地图"], horizontal=True)
        st.markdown("---")
        st.markdown("### ⚙️ 航线参数配置")

        colA1, colA2 = st.columns(2)
        with colA1:
            st.markdown("#### 起点 A")
            latA = st.number_input("纬度", value=32.2335, format="%.6f")
        with colA2:
            st.markdown("#### ")
            lngA = st.number_input("经度", value=118.7475, format="%.6f")

        colB1, colB2 = st.columns(2)
        with colB1:
            st.markdown("#### 终点 B")
            latB = st.number_input("纬度 ", value=32.2338, format="%.6f")
        with colB2:
            st.markdown("#### ")
            lngB = st.number_input("经度 ", value=118.7479, format="%.6f")

        components.html(render_map(latA, lngA, latB, lngB, map_switch), height=700)

    # -------------------------- 心跳监测（新增暂停键） --------------------------
    else:
        st.title("📡 无人机通信心跳监测可视化")

        # 初始化状态
        if "heartbeat_data" not in st.session_state:
            st.session_state.heartbeat_data = []
            st.session_state.seq = 0
            st.session_state.last_receive_time = time.time()
            st.session_state.running = False  # 运行状态

        col_start, col_stop = st.columns(2)
        with col_start:
            if st.button("▶️ 开始监测"):
                st.session_state.running = True
        with col_stop:
            if st.button("⏸️ 暂停监测"):
                st.session_state.running = False
                st.info("监测已暂停")

        def simulate_heartbeat():
            st.session_state.seq += 1
            t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.last_receive_time = time.time()
            st.session_state.heartbeat_data.append({
                "seq": st.session_state.seq, "time": t, "status": "received"
            })

        def check_timeout():
            if time.time() - st.session_state.last_receive_time > 3:
                t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.heartbeat_data.append({
                    "seq": st.session_state.seq, "time": t, "status": "timeout"
                })
                st.warning("⚠️ 连接超时！3秒未收到心跳包！")

        placeholder = st.empty()
        if st.session_state.running:
            while st.session_state.running:
                simulate_heartbeat()
                check_timeout()
                df = pd.DataFrame(st.session_state.heartbeat_data)
                with placeholder.container():
                    st.subheader("📈 心跳包时序图")
                    st.line_chart(df, x="time", y="seq", color="status")
                    st.subheader("📋 原始数据")
                    st.dataframe(df, use_container_width=True)
                time.sleep(1)
