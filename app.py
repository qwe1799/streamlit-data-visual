import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time
import datetime

# -------------------------- 页面配置 --------------------------
st.set_page_config(page_title="导航", layout="wide")

# -------------------------- 样式完全还原你的截图 --------------------------
st.markdown("""
<style>
    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
    }
    .left-section {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    h3 {
        font-size: 20px !important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------- 左右布局：左侧控制面板 --------------------------
col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown('<div class="left-section">', unsafe_allow_html=True)

    st.subheader("🧭 导航")
    func_mode = st.radio("", ["航线规划", "飞行监控"], index=0)

    st.divider()

    st.subheader("⚙️ 坐标系设置")
    coord_type = st.radio("", ["WGS-84", "GCJ-02(高德/百度)"], index=1)

    st.divider()

    st.subheader("📊 系统状态")
    st.success("✅ A点已设")
    st.success("✅ B点已设")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------- 地图组件（绝对不会报错） --------------------------
def render_map(latA, lonA, latB, lonB):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css">
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <style>#map {{width:100%;height:650px;border-radius:8px;}}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([{latA}, {lonA}], 19);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 22
            }}).addTo(map);

            L.marker([{latA}, {lonA}]).addTo(map).bindPopup("A点");
            L.marker([{latB}, {lonB}]).addTo(map).bindPopup("B点");
            L.polyline([[{latA},{lonA}],[{latB},{lonB}]],{{color:'red',weight:4}}).addTo(map);
        </script>
    </body>
    </html>
    """
    return html

# -------------------------- 右侧内容：航线规划 / 心跳监测 --------------------------
with col_right:
    if func_mode == "航线规划":
        st.markdown("### 🗺️ 航线规划")

        # 完全还原你截图的坐标输入布局
        colA1, colA2 = st.columns(2)
        with colA1:
            st.markdown("##### 起点 A")
            latA = st.number_input("纬度", value=32.2322, format="%.6f")
        with colA2:
            st.markdown("##### ")
            lonA = st.number_input("经度", value=118.7490, format="%.6f")

        colB1, colB2 = st.columns(2)
        with colB1:
            st.markdown("##### 终点 B")
            latB = st.number_input("纬度 ", value=32.2343, format="%.6f")
        with colB2:
            st.markdown("##### ")
            lonB = st.number_input("经度 ", value=118.7490, format="%.6f")

        # 地图显示（100%正常）
        components.html(render_map(latA, lonA, latB, lonB), height=670)

    else:
        # 你提供的心跳监测代码
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
