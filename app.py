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
</style>
""", unsafe_allow_html=True)

# -------------------------- 地图核心（高德普通图 + ArcGIS卫星图 + 坐标在校内） --------------------------
def render_map(latA, lngA, latB, lngB, map_type):
    # 1. 选择地图图层
    if map_type == "卫星影像地图":
        # 卫星图：ArcGIS高清航拍
        layer_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attribution = 'Tiles © Esri'
    else:
        # 普通图：高德地图（国内最稳，无密钥直接用）
        layer_url = "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
        attribution = '© 高德地图'

    # 2. 字符串拼接彻底避免f-string语法错误
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
            // 地图中心点：南京科技职业学院校内（精准校正，不再偏右）
            var map = L.map('map').setView([32.2336, 118.7478], 18);
            
            // 加载选中的地图图层
            L.tileLayer('""" + layer_url + """', {
                maxZoom: 20,
                attribution: '""" + attribution + """'
            }).addTo(map);

            // A点：南京科技职业学院校内核心
            L.marker([""" + str(latA) + """, """ + str(lngA) + """]).addTo(map)
                .bindPopup("✅ 起点A - 南科院");
                
            // B点：南京科技职业学院校内
            L.marker([""" + str(latB) + """, """ + str(lngB) + """]).addTo(map)
                .bindPopup("✅ 终点B - 南科院");

            // 红色航线
            L.polyline([
                [""" + str(latA) + """, """ + str(lngA) + """],
                [""" + str(latB) + """, """ + str(lngB) + """]
            ], {color:"red", weight:5, opacity:0.8}).addTo(map);
        </script>
    </body>
    </html>
    """
    return html

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
        # 地图模式切换（高德普通图 / ArcGIS卫星图）
        map_switch = st.radio("🗺️ 地图模式", ["高德普通地图", "卫星影像地图"], horizontal=True)

        st.markdown("---")
        st.markdown("### ⚙️ 航线参数配置")

        # ✅ A点：南京科技职业学院校内（彻底解决偏右）
        colA1, colA2 = st.columns(2)
        with colA1:
            st.markdown("#### 起点 A")
            latA = st.number_input("纬度", value=32.2336, format="%.6f", step=0.0001, key="latA")
        with colA2:
            st.markdown("#### ")
            lngA = st.number_input("经度", value=118.7478, format="%.6f", step=0.0001, key="lngA")

        # ✅ B点：南京科技职业学院校内
        colB1, colB2 = st.columns(2)
        with colB1:
            st.markdown("#### 终点 B")
            latB = st.number_input("纬度 ", value=32.2339, format="%.6f", step=0.0001, key="latB")
        with colB2:
            st.markdown("#### ")
            lngB = st.number_input("经度 ", value=118.7482, format="%.6f", step=0.0001, key="lngB")

        # 渲染地图（100%显示）
        components.html(render_map(latA, lngA, latB, lngB, map_switch), height=700)

    else:
        # 心跳监测页面（保持你的核心逻辑）
        st.title("📡 无人机通信心跳监测可视化")

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
