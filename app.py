import streamlit as st
import streamlit_folium as st_folium
import folium
import pandas as pd
import time
import datetime
import json
import os

# ==================== 页面配置 ====================
st.set_page_config(page_title="无人机地面站", layout="wide")

# ==================== 样式 ====================
st.markdown("""
<style>
.left-panel {background:#f8f9fa; padding:20px; border-radius:10px; height:95vh;}
</style>
""", unsafe_allow_html=True)

# ==================== 持久化 ====================
STATE_FILE = "ground_station_state.json"

def save_state():
    state = {
        "obstacles": st.session_state.obstacles,
        "draw_points": st.session_state.draw_points,
        "home_point": st.session_state.home_point,
        "waypoints": st.session_state.waypoints
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ==================== 初始化 ====================
if "init" not in st.session_state:
    loaded = load_state()
    st.session_state.obstacles = loaded.get("obstacles", [])
    st.session_state.draw_points = loaded.get("draw_points", [])
    st.session_state.home_point = loaded.get("home_point", [32.2335, 118.7475])
    st.session_state.waypoints = loaded.get("waypoints", [])
    st.session_state.last_click = None
    st.session_state.heartbeat_data = []
    st.session_state.seq = 0
    st.session_state.running = False
    st.session_state.init = True

# ==================== 左侧 ====================
col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)
    st.subheader("🧭 导航")
    page = st.radio("", ["航线规划", "飞行监控"], label_visibility="collapsed")
    st.divider()

    if page == "航线规划":
        st.markdown("### 🚧 障碍物圈选")
        name = st.text_input("障碍物名称", "教学楼")
        height = st.number_input("高度(m)", 1, 500, 25)

        st.info(f"当前已打点：{len(st.session_state.draw_points)} 个")

        if st.button("🧹 清空当前打点", use_container_width=True):
            st.session_state.draw_points = []
            save_state()
            st.rerun()

        if st.button("✅ 保存障碍物", type="primary", use_container_width=True):
            if len(st.session_state.draw_points) >= 3:
                st.session_state.obstacles.append({
                    "name": name,
                    "height": height,
                    "points": st.session_state.draw_points.copy()
                })
                st.session_state.draw_points = []
                save_state()
                st.success("✅ 保存成功！")
                st.rerun()
            else:
                st.warning("至少3个点")

        st.divider()
        st.markdown("### 📋 已保存障碍物")
        for i, ob in enumerate(st.session_state.obstacles):
            c1, c2 = st.columns([3,1])
            with c1:
                st.write(f"📍 {ob['name']}")
            with c2:
                if st.button("删除", key=f"del{i}", use_container_width=True):
                    del st.session_state.obstacles[i]
                    save_state()
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 右侧 ====================
with col_right:
    st.markdown("# 南京科技职业学院")
    st.markdown("## 无人机航线导航与监控系统")

    if page == "航线规划":
        # -------------------------- AB点（起点/终点）100% 还原 --------------------------
        st.markdown("### 🎯 AB点航线")
        c1, c2 = st.columns(2)
        with c1:
            latA = st.number_input("起点纬度", value=32.2335, format="%.6f")
            lngA = st.number_input("起点经度", value=118.7475, format="%.6f")
        with c2:
            latB = st.number_input("终点纬度", value=32.2338, format="%.6f")
            lngB = st.number_input("终点经度", value=118.7479, format="%.6f")

        fly_h = st.number_input("飞行高度(m)", min_value=1, value=50)

        # -------------------------- 地图（正常显示！） --------------------------
        m = folium.Map(location=[latA, lngA], zoom_start=17)

        # AB点航线
        folium.PolyLine(
            locations=[[latA, lngA], [latB, lngB]],
            color="red", weight=5
        ).add_to(m)

        # 起点标记
        folium.Marker([latA, lngA], popup="起点A", icon=folium.Icon(color="green")).add_to(m)
        # 终点标记
        folium.Marker([latB, lngB], popup="终点B", icon=folium.Icon(color="red")).add_to(m)

        # 障碍物
        for ob in st.session_state.obstacles:
            ps = [[lat, lng] for (lng, lat) in ob["points"]]
            folium.Polygon(locations=ps, color="red", fill=True, fill_opacity=0.5).add_to(m)

        # 当前圈选
        if len(st.session_state.draw_points) >= 2:
            ps = [[lat, lng] for (lng, lat) in st.session_state.draw_points]
            folium.PolyLine(locations=ps, color="blue", weight=4).add_to(m)

        # 地图显示（关键修复！）
        o = st_folium.st_folium(m, width=1400, height=700)

        # 点击打点
        if o and o.get("last_clicked"):
            lat = o["last_clicked"]["lat"]
            lng = o["last_clicked"]["lng"]
            pt = (round(lng,6), round(lat,6))
            if pt != st.session_state.last_click:
                st.session_state.last_click = pt
                st.session_state.draw_points.append(pt)
                save_state()
                st.rerun()

    else:
        # 心跳监控
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
                st.session_state.seq +=1
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
                time.sleep(0.5)
