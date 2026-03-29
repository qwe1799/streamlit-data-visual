import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
import datetime

# -------------------------- 页面配置 --------------------------
st.set_page_config(page_title="导航系统", layout="wide")

# -------------------------- 样式 --------------------------
st.markdown("""
<style>
.left-panel {
    background-color: #f5f5f5;
    padding: 25px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------- 地图（100%无语法错误） --------------------------
def map_html(latA, lngA, latB, lngB):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css">
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>#map {width:100%;height:650px;border-radius:10px;}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView(["""+str(latA)+""", """+str(lngA)+"""], 18);
            L.tileLayer('https://tile.openstreetmap.de/{z}/{x}/{y}.png', {
                maxZoom: 19
            }).addTo(map);

            L.marker(["""+str(latA)+""", """+str(lngA)+"""]).addTo(map).bindPopup("A点");
            L.marker(["""+str(latB)+""", """+str(lngB)+"""]).addTo(map).bindPopup("B点");

            L.polyline([
                ["""+str(latA)+""", """+str(lngA)+"""],
                ["""+str(latB)+""", """+str(lngB)+"""]
            ], {color:"red",weight:5,opacity:0.8}).addTo(map);
        </script>
    </body>
    </html>
    """

# -------------------------- 布局 --------------------------
col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)

    st.subheader("🧭 导航")
    page = st.radio("", ["航线规划", "飞行监控"], index=0)

    st.divider()

    st.subheader("⚙️ 坐标系设置")
    coord = st.radio("", ["WGS-84", "GCJ-02(高德/百度)"], index=1)

    st.divider()

    st.subheader("📊 系统状态")
    st.success("✅ A点已设")
    st.success("✅ B点已设")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 右侧内容 --------------------------
with col_right:
    if page == "航线规划":
        st.markdown("## 🗺️ 航线规划")

        colA1, colA2 = st.columns(2)
        with colA1:
            st.markdown("##### 起点 A")
            latA = st.number_input("纬度", value=32.2322, format="%.6f")
        with colA2:
            st.markdown("##### ")
            lngA = st.number_input("经度", value=118.7490, format="%.6f")

        colB1, colB2 = st.columns(2)
        with colB1:
            st.markdown("##### 终点 B")
            latB = st.number_input("纬度 ", value=32.2343, format="%.6f")
        with colB2:
            st.markdown("##### ")
            lngB = st.number_input("经度 ", value=118.7490, format="%.6f")

        # 地图
        components.html(map_html(latA, lngA, latB, lngB), height=670)

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
                st.warning("⚠️ 连接超时！3秒未收到心跳包！")

        if st.button("开始监测"):
            placeholder = st.empty()
            while True:
                simulate_heartbeat()
                check_timeout()
                df = pd.DataFrame(st.session_state.heartbeat_data)
                with placeholder.container():
                    st.subheader("心跳包时序图")
                    st.line_chart(df, x="time", y="seq", color="status")
                    st.subheader("原始数据")
                    st.dataframe(df)
                time.sleep(1)
