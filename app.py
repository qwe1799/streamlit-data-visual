import streamlit as st
import streamlit_folium as st_folium
import folium
from folium import TileLayer
import pandas as pd
import time
import datetime
import json
import os

# ==================== 页面配置 ====================
st.set_page_config(page_title="南京科技职业学院 - 无人机导航系统", layout="wide")

# ==================== 样式 ====================
st.markdown("""
<style>
.left-panel {background:#f8f9fa; padding:20px; border-radius:10px; height:95vh;}
</style>
""", unsafe_allow_html=True)

# ==================== 持久化（你给的稳定版） ====================
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

# ==================== 右侧布局 ====================
with col_right:
    st.markdown("# 🎓 南京科技职业学院")
    st.markdown("## 无人机航线导航与监控系统")

    if page == "航线规划":
        # ==================== AB点（顺序修正：A=起点，B=终点） ====================
        st.markdown("### 🎯 AB点航线")
        c1, c2 = st.columns(2)
        with c1:
            latA = st.number_input("起点A纬度", value=32.233500, format="%.6f")
            lngA = st.number_input("起点A经度", value=118.747500, format="%.6f")
        with c2:
            latB = st.number_input("终点B纬度", value=32.233800, format="%.6f")
            lngB = st.number_input("终点B经度", value=118.747900, format="%.6f")

        fly_h = st.number_input("飞行高度(m)", min_value=1, max_value=500, value=50, step=1)

        # ==================== 地图模式切换（高德/卫星，完全还原） ====================
        map_type = st.radio("🗺️ 地图模式", ["高德普通地图", "卫星影像地图"], horizontal=True)

        # ==================== 初始化地图（修复空白问题） ====================
        center_lat = (latA + latB) / 2
        center_lng = (lngA + lngB) / 2
        m = folium.Map(location=[center_lat, center_lng], zoom_start=17, control_scale=True)

        # ==================== 添加地图图层 ====================
        if map_type == "卫星影像地图":
            # 卫星图层
            TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri",
                name="卫星影像",
                max_zoom=20
            ).add_to(m)
        else:
            # 高德普通地图
            TileLayer(
                tiles="https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}",
                attr="© 高德",
                name="高德地图",
                max_zoom=20
            ).add_to(m)

        # ==================== AB点航线（顺序正确） ====================
        folium.PolyLine(
            locations=[[latA, lngA], [latB, lngB]],
            color="red",
            weight=5,
            opacity=0.8
        ).add_to(m)

        # 起点A（绿色）
        folium.Marker(
            [latA, lngA],
            popup="起点A",
            icon=folium.Icon(color="green", icon="info-sign")
        ).add_to(m)

        # 终点B（红色）
        folium.Marker(
            [latB, lngB],
            popup="终点B",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

        # ==================== 障碍物绘制（你给的稳定逻辑） ====================
        for ob in st.session_state.obstacles:
            ps = [[lat, lng] for (lng, lat) in ob["points"]]
            folium.Polygon(
                locations=ps,
                color="red",
                fill=True,
                fill_opacity=0.5,
                popup=f"{ob['name']} ({ob['height']}m)"
            ).add_to(m)

        # ==================== 当前圈选（蓝色临时多边形） ====================
        if len(st.session_state.draw_points) >= 2:
            ps = [[lat, lng] for (lng, lat) in st.session_state.draw_points]
            folium.Polygon(
                locations=ps,
                color="blue",
                fill=True,
                fill_opacity=0.2
            ).add_to(m)

        # ==================== 地图渲染（修复空白，强制加载） ====================
        o = st_folium.st_folium(
            m,
            width=1400,
            height=700,
            returned_objects=["last_clicked"]
        )

        # ==================== 点击打点（你给的稳定逻辑） ====================
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
        # ==================== 心跳监控（完整保留原有功能） ====================
        st.title("📡 无人机心跳监控")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶️ 开始监测", use_container_width=True):
                st.session_state.running = True
        with c2:
            if st.button("⏸️ 暂停监测", use_container_width=True):
                st.session_state.running = False

        placeholder = st.empty()
        while True:
            if st.session_state.running:
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
            else:
                time.sleep(0.5)
