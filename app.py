import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
import datetime

# -------------------------- 页面配置 --------------------------
st.set_page_config(
    page_title="南京科技职业学院 - 无人机导航系统",
    layout="wide"
)

# -------------------------- 样式还原截图 --------------------------
st.markdown("""
<style>
.left-panel {
    background-color: #f8f9fa;
    padding: 25px;
    border-radius: 10px;
    height: 100vh;
}
/* 坐标输入框样式 */
.css-1n543ie {
    min-width: 180px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------- 地图核心（普通/卫星切换 + 南京科技职院精准坐标） --------------------------
def map_html(latA, lngA, latB, lngB, map_type):
    # 配置两种地图图层
    if map_type == "卫星地图":
        # 卫星图（ArcGIS，清晰度高）
        layer_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}"
    else:
        # 普通街道图
        layer_url = "https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css">
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>#map {{width:100%;height:680px;border-radius:10px;}}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            // 地图中心点：南京科技职业学院（确保在学校内）
            var map = L.map('map').setView([32.2340, 118.7485], 17);

            // 加载选中的地图
            L.tileLayer('{layer_url}', {{
                maxZoom: 20,
                attribution: '© OpenStreetMap/ArcGIS'
            }}).addTo(map);

            // A点：南京科技职业学院内（精确修正，确保在校内）
            var markerA = L.marker([32.2338, 118.7482]).addTo(map)
                .bindPopup("✅ 起点A - 南京科技职业学院");
                
            // B点：南京科技职业学院内（精确修正）
            var markerB = L.marker([32.2342, 118.7488]).addTo(map)
                .bindPopup("✅ 终点B - 南京科技职业学院");

            // 绘制航线（红色）
            L.polyline([
                [32.2338, 118.7482],
                [32.2342, 118.7488]
            ], {{color:"red", weight:6, opacity:0.9}}).addTo(map);
        </script>
    </body>
    </html>
    """

# -------------------------- 左侧布局（还原你的截图） --------------------------
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

# -------------------------- 右侧内容 --------------------------
with col_right:
    st.markdown("# 🎓 南京科技职业学院")
    st.markdown("### 无人机航线导航与监控系统")

    if page == "航线规划":
        # 地图模式切换（普通/卫星）
        map_switch = st.radio("🗺️ 地图模式", ["普通街道地图", "卫星影像地图"], horizontal=True)

        st.markdown("---")
        st.markdown("### ⚙️ 航线参数配置")

        # A点输入（默认值已校准为学校内）
        colA1, colA2 = st.columns(2)
        with colA1:
            st.markdown("#### 起点 A")
            latA = st.number_input("纬度", value=32.2338, format="%.6f", step=0.0001, key="latA")
        with colA2:
            st.markdown("#### ")
            lngA = st.number_input("经度", value=118.7482, format="%.6f", step=0.0001, key="lngA")

        # B点输入（默认值已校准为学校内）
        colB1, colB2 = st.columns(2)
        with colB1:
            st.markdown("#### 终点 B")
            latB = st.number_input("纬度 ", value=32.2342, format="%.6f", step=0.0001, key="latB")
        with colB2:
            st.markdown("#### ")
            lngB = st.number_input("经度 ", value=118.7488, format="%.6f", step=0.0001, key="lngB")

        # 显示地图
        components.html(map_html(latA, lngA, latB, lngB, map_switch), height=700)

    else:
        # 心跳监测页面（保持你的核心逻辑）
        st.title("📡 无人机通信心跳监测可视化")
        st.markdown("### 南京科技职业学院 无人机项目")

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
                st.warning("⚠️ 连接超时！3秒未收到心跳包！")

        if st.button("▶️ 开始监测"):
            placeholder = st.empty()
            while True:
                simulate_heartbeat()
                check_timeout()
                df = pd.DataFrame(st.session_state.heartbeat_data)
                with placeholder.container():
                    st.subheader("📈 心跳包时序图")
                    st.line_chart(df, x="time", y="seq", color="status")
                    st.subheader("📋 原始数据")
                    st.dataframe(df, use_container_width=True)
                time.sleep(1)
