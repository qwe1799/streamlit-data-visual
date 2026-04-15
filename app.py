import streamlit as st
import streamlit.components.v1 as components
import streamlit_folium as st_folium
import folium
import pandas as pd
import time
import datetime
import json
import os
import math

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="南京科技职业学院 - 无人机导航系统",
    layout="wide"
)

# ==================== 样式 ====================
st.markdown("""
<style>
.left-panel {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    height: 95vh;
}
</style>
""", unsafe_allow_html=True)

# ==================== 持久化状态（你提供的稳定版） ====================
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

    # 心跳监控状态
    st.session_state.heartbeat_data = []
    st.session_state.seq = 0
    st.session_state.running = False
    st.session_state.init = True

# ==================== 坐标转换 ====================
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

# ==================== 左侧布局 ====================
col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)
    st.subheader("🧭 导航")
    page = st.radio("", ["航线规划", "飞行监控"], label_visibility="collapsed")
    st.divider()

    if page == "航线规划":
        st.markdown("### 🚧 障碍物圈选（永久记忆）")
        name = st.text_input("障碍物名称", "教学楼")
        height = st.number_input("高度(m)", min_value=1, max_value=500, value=25, step=1)

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
                st.success("✅ 保存成功！永久显示！")
                st.rerun()
            else:
                st.warning("⚠️ 至少需要3个点")

        st.divider()
        st.markdown("### 📋 已保存障碍物")
        for i, ob in enumerate(st.session_state.obstacles):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"📍 {ob['name']} ({ob['height']}m)")
            with c2:
                if st.button("🗑️ 删除", key=f"del_{i}", use_container_width=True):
                    del st.session_state.obstacles[i]
                    save_state()
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ==================== 右侧 ====================
with col_right:
    st.markdown("# 🎓 南京科技职业学院")
    st.markdown("## 无人机航线导航与监控系统")

    if page == "航线规划":
        # 原有功能：飞行高度、起点终点、地图
        map_type = st.radio("🗺️ 地图模式", ["普通地图", "卫星地图"], horizontal=True)
        fly_h = st.number_input("飞行高度(m)", min_value=1, max_value=500, value=50)

        c1, c2 = st.columns(2)
        with c1:
            latA = st.number_input("起点纬度", value=32.2335, format="%.6f")
            lngA = st.number_input("起点经度", value=118.7475, format="%.6f")
        with c2:
            latB = st.number_input("终点纬度", value=32.2338, format="%.6f")
            lngB = st.number_input("终点经度", value=118.7479, format="%.6f")

        # ==================== 地图（替换成你的稳定圈选逻辑） ====================
        m = folium.Map(location=[latA, lngA], zoom_start=17)

        # 航线
        folium.PolyLine(
            locations=[[latA, lngA], [latB, lngB]],
            color='red', weight=4
        ).add_to(m)

        # 障碍物（你的稳定代码）
        for ob in st.session_state.obstacles:
            ps = [[lat, lng] for lng, lat in ob['points']]
            folium.Polygon(
                locations=ps, color='red', fill=True, fill_opacity=0.5
            ).add_to(m)

        # 当前圈选
        if len(st.session_state.draw_points) >= 2:
            ps = [[lat, lng] for lng, lat in st.session_state.draw_points]
            folium.Polygon(
                locations=ps, color='blue', fill=True, fill_opacity=0.2
            ).add_to(m)

        o = st_folium.st_folium(m, width=1200, height=680)

        # 点击打点（你的稳定逻辑）
        if o and o.get("last_clicked"):
            lat = o["last_clicked"]["lat"]
            lng = o["last_clicked"]["lng"]
            pt = (round(lng, 6), round(lat, 6))
            if pt != st.session_state.last_click:
                st.session_state.last_click = pt
                st.session_state.draw_points.append(pt)
                save_state()
                st.rerun()

    else:
        # 原有功能：心跳监控 100% 保留
        st.title("📡 无人机心跳监控")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶️ 开始监测", use_container_width=True):
                st.session_state.running = True
        with c2:
            if st.button("⏸️ 暂停监测", use_container_width=True):
                st.session_state.running = False

        placeholder = st.empty()
        if st.session_state.running:
            while st.session_state.running:
                st.session_state.seq += 1
                t = datetime.datetime.now().strftime("%H:%M:%S")
                st.session_state.heartbeat_data.append({
                    "序号": st.session_state.seq,
                    "时间": t,
                    "状态": "正常"
                })
                df = pd.DataFrame(st.session_state.heartbeat_data)
                with placeholder.container():
                    st.line_chart(df, x="时间", y="序号")
                    st.dataframe(df, use_container_width=True)
                time.sleep(1)
