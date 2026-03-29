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

# -------------------------- 自定义CSS（还原图片样式） --------------------------
st.markdown("""
<style>
/* 全局样式 */
.stApp {
    background-color: #f5f7fa;
}
/* 左侧面板样式 */
.left-panel {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 8px;
}
/* 标题样式 */
.main-title {
    font-size: 28px;
    font-weight: bold;
    color: #333;
    margin: 10px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
/* 子标题样式 */
.sub-title {
    font-size: 18px;
    color: #666;
    margin: 20px 0 10px 0;
}
/* 状态标签样式 */
.status-tag {
    background-color: #e6f4ea;
    color: #2e7d32;
    padding: 10px 15px;
    border-radius: 8px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
}
/* 单选按钮组样式 */
.row-widget.stRadio > div {
    flex-direction: column;
    gap: 10px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------- 坐标系转换工具函数 --------------------------
def gcj02_to_wgs84(lat, lng):
    """GCJ-02转WGS-84（国测局转地球坐标系）"""
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

# -------------------------- 地图HTML（修复加载问题） --------------------------
def map_html(lat_a, lng_a, lat_b, lng_b, coord_type):
    # 坐标系转换
    if coord_type == "GCJ-02(高德/百度)":
        lat_a, lng_a = gcj02_to_wgs84(lat_a, lng_a)
        lat_b, lng_b = gcj02_to_wgs84(lat_b, lng_b)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>#map {{ width: 100%; height: 600px; border-radius: 8px; }}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{lat_a}, {lng_a}], 19);
            // 稳定底图
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {{
                attribution: '&copy; OpenStreetMap contributors',
                maxZoom: 22
            }}).addTo(map);
            
            // 绘制A点、B点、航线
            L.marker([{lat_a}, {lng_a}], {{icon: L.divIcon({{html: '<span style="color:red; font-size:30px;">📍</span>'}})}})
              .addTo(map).bindPopup("起点A");
            L.marker([{lat_b}, {lng_b}], {{icon: L.divIcon({{html: '<span style="color:green; font-size:30px;">▶️</span>'}})}})
              .addTo(map).bindPopup("终点B");
            L.polyline([[{lat_a}, {lng_a}], [{lat_b}, {lng_b}]], {{color: 'red', weight: 5, opacity: 0.8}}).addTo(map);
        </script>
    </body>
    </html>
    """

# -------------------------- 主界面布局（左侧控制面板 + 右侧地图） --------------------------
col_left, col_right = st.columns([1, 3])  # 左侧:右侧 = 1:3

with col_left:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)
    
    # 导航模块
    st.markdown('<p class="main-title">🧭 导航</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">功能页面</p>', unsafe_allow_html=True)
    page = st.radio(
        "",
        options=["📖 航线规划", "✈️ 飞行监控"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # 坐标系设置
    st.markdown('<p class="main-title">⚙️ 坐标系设置</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">输入坐标系</p>', unsafe_allow_html=True)
    coord_type = st.radio(
        "",
        options=["WGS-84", "GCJ-02(高德/百度)"],
        index=1,
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # 系统状态
    st.markdown('<p class="main-title">📊 系统状态</p>', unsafe_allow_html=True)
    st.markdown('<div class="status-tag">✅ A点已设</div>', unsafe_allow_html=True)
    st.markdown('<div class="status-tag">✅ B点已设</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    if page == "📖 航线规划":
        st.markdown("### 🗺️ 地图")
        # 坐标输入（默认值为图片中的坐标）
        col_a, col_b = st.columns(2)
        with col_a:
            lat_a = st.number_input("A点纬度", value=32.2322, format="%.6f", step=0.0001)
            lng_a = st.number_input("A点经度", value=118.749, format="%.6f", step=0.0001)
        with col_b:
            lat_b = st.number_input("B点纬度", value=32.2343, format="%.6f", step=0.0001)
            lng_b = st.number_input("B点经度", value=118.749, format="%.6f", step=0.0001)
        
        # 渲染地图
        components.html(map_html(lat_a, lng_a, lat_b, lng_b, coord_type), height=620)
    
    else:
        # 飞行监控（心跳监测）
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
                    st.dataframe(df)
                    
                time.sleep(1)
