import streamlit as st
import pandas as pd
import time
import datetime

# -------------------------- 页面配置 --------------------------
st.set_page_config(page_title="无人机导航系统", layout="wide")

# -------------------------- 地图显示函数（100%兼容Streamlit） --------------------------
def show_map(lat1, lon1, lat2, lon2):
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>#map {{width: 100%; height: 500px;}}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{lat1}, {lon1}], 18);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 22
            }}).addTo(map);
            
            L.marker([{lat1}, {lon1}]).addTo(map).bindPopup("A点");
            L.marker([{lat2}, {lon2}]).addTo(map).bindPopup("B点");
            L.polyline([[{lat1},{lon1}], [{lat2},{lon2}]], {{color: 'red', weight: 5}}).addTo(map);
        </script>
    </body>
    </html>
    """
    return map_html

# -------------------------- 界面 --------------------------
st.title("🧭 无人机航线导航系统")

# 页面切换
tab1, tab2 = st.tabs(["航线规划", "飞行监控"])

# -------------------------- 航线规划（地图正常显示） --------------------------
with tab1:
    st.subheader("🗺️ 航线规划")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📍 A点坐标")
        lat1 = st.number_input("A点纬度", value=32.2322, format="%.6f")
        lon1 = st.number_input("A点经度", value=118.7490, format="%.6f")
        
    with col2:
        st.markdown("#### 📍 B点坐标")
        lat2 = st.number_input("B点纬度", value=32.2343, format="%.6f")
        lon2 = st.number_input("B点经度", value=118.7490, format="%.6f")

    st.success("✅ 地图加载成功！")
    components = st.components.v1.html(show_map(lat1, lon1, lat2, lon2), height=520)

# -------------------------- 心跳监测（你提供的代码） --------------------------
with tab2:
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
                st.dataframe(df)
                
            time.sleep(1)
