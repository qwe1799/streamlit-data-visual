import streamlit as st
import streamlit.components.v1 as components
import math
import pandas as pd
import time
import datetime

# -------------------------- 页面基础配置 --------------------------
st.set_page_config(
    page_title="校园导航系统",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------- 自定义CSS --------------------------
st.markdown("""
<style>
.stApp {
    background-color: #f5f7fa;
    max-width: 1200px;
    margin: 0 auto;
}
.main-title {
    font-size: 22px;
    font-weight: bold;
    color: #333;
    margin: 10px 0;
}
.divider {
    margin: 15px 0;
    border-top: 1px solid #eee;
}
.status-box {
    background-color: #e6f4ea;
    color: #2e7d32;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 5px 0;
    font-size: 15px;
}
.row-widget.stRadio > div {
    flex-direction: row;
    gap: 15px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------- 坐标系转换 --------------------------
def gcj02_to_wgs84(lat, lng):
    a = 6378245.0
    ee = 0.00669342162296594323
    dLat = _transform_lat(lng - 105.0, lat - 35.0)
    dLng = _transform_lng(lng - 105.0, lat - 35.0)
    radLat = lat / 180.0 * math.pi
    magic = math.sin(radLat)
    magic = 1 - ee * magic * magic
    sqrtMagic = math.sqrt(magic)
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * math.pi)
    dLng = (dLng * 180.0) / (a / sqrtMagic * math.cos(radLat) * math.pi)
    mgLat = lat + dLat
    mgLng = lng + dLng
    return round(lat * 2 - mgLat, 6), round(lng * 2 - mgLng, 6)

def _transform_lat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret

def _transform_lng(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret

# -------------------------- 校内范围 --------------------------
def is_in_campus(lat, lng):
    return 32.230 <= lat <= 32.240 and 118.745 <= lng <= 118.755

# -------------------------- 地图 --------------------------
def map_html(lat_a, lng_a, lat_b, lng_b, coord_type):
    if coord_type == "GCJ-02(高德/百度)":
        lat_a, lng_a = gcj02_to_wgs84(lat_a, lng_a)
        lat_b, lng_b = gcj02_to_wgs84(lat_b, lng_b)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>#map {{ height: 600px; width: 100%; border-radius: 8px; }}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{lat_a}, {lng_a}], 19);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
            L.marker([{lat_a}, {lng_a}]).addTo(map).bindPopup("A点");
            L.marker([{lat_b}, {lng_b}]).addTo(map).bindPopup("B点");
            L.polyline([[{lat_a}, {lng_a}], [{lat_b}, {lng_b}]], {{color:'red',weight:4}}).addTo(map);
        </script>
    </body>
    </html>
    """

# -------------------------- 界面 --------------------------
st.markdown('<p class="main-title">🧭 导航</p>', unsafe_allow_html=True)
page = st.radio("", ["航线规划", "飞行监控"], index=0)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.markdown('<p class="main-title">⚙️ 坐标系设置</p>', unsafe_allow_html=True)
coord_type = st.radio("", ["WGS-84", "GCJ-02(高德/百度)"], index=1)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# -------------------------- 航线规划 --------------------------
if page == "航线规划":
    col_map, col_ctrl = st.columns([2, 1])

    with col_ctrl:
        st.markdown("### 控制面板")
        st.markdown("#### 起点 A")
        lat_a = st.number_input("A纬度", value=32.2322, format="%.6f")
        lng_a = st.number_input("A经度", value=118.7490, format="%.6f")

        st.markdown("#### 终点 B")
        lat_b = st.number_input("B纬度", value=32.2343, format="%.6f")
        lng_b = st.number_input("B经度", value=118.7490, format="%.6f")

    with col_map:
        st.markdown("### 🗺️ 地图")
        a_ok = is_in_campus(lat_a, lng_a)
        b_ok = is_in_campus(lat_b, lng_b)

        if a_ok and b_ok:
            st.success("✅ A、B点均在校内")
            components.html(map_html(lat_a, lng_a, lat_b, lng_b, coord_type), height=620)
        else:
            st.error("❌ 坐标超出范围")

# -------------------------- 心跳监测（你提供的代码，已修复死循环） --------------------------
else:
    st.title("无人机通信心跳监测可视化")

    if "heartbeat_data" not in st.session_state:
        st.session_state.heartbeat_data = []
        st.session_state.seq = 0
        st.session_state.last_receive_time = time.time()

    def simulate_heartbeat():
        st.session_state.seq += 1
        t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.last_receive_time = time.time()
        st.session_state.heartbeat_data.append({
            "seq": st.session_state.seq,
            "time": t,
            "status": "received"
        })

    def check_timeout():
        if time.time() - st.session_state.last_receive_time > 3:
            t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.heartbeat_data.append({
                "seq": st.session_state.seq,
                "time": t,
                "status": "timeout"
            })
            st.warning("⚠️ 3秒未收到心跳！")

    if st.button("开始监测"):
        placeholder = st.empty()
        while True:
            simulate_heartbeat()
            check_timeout()
            df = pd.DataFrame(st.session_state.heartbeat_data)
            
            with placeholder.container():
                st.subheader("心跳时序图")
                st.line_chart(df, x="time", y="seq", color="status")
                st.subheader("原始数据")
                st.dataframe(df, use_container_width=True)
                
            time.sleep(1)
