import streamlit as st
import streamlit_folium as st_folium
import folium
import pandas as pd
import json
import os
import time
import datetime

# ==================== 页面配置 ====================
st.set_page_config(page_title="无人机地面站", layout="wide")

# ==================== 持久化文件（你给的稳定方案） ====================
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

# ==================== 初始化状态（真正记忆！） ====================
if "init" not in st.session_state:
    loaded = load_state()
    st.session_state.obstacles = loaded.get("obstacles", [])
    st.session_state.draw_points = loaded.get("draw_points", [])
    st.session_state.home_point = loaded.get("home_point", [32.2335, 118.7475])
    st.session_state.waypoints = loaded.get("waypoints", [])
    st.session_state.last_click = None
    st.session_state.init = True

# ==================== 左侧UI ====================
col_left, col_right = st.columns([1, 3])

with col_left:
    st.subheader("🚧 障碍物圈选（永久记忆版）")
    name = st.text_input("障碍物名称", "教学楼")
    height = st.number_input("高度(m)", 1, 500, 25)

    # 实时显示打点数量
    st.info(f"当前已打点：{len(st.session_state.draw_points)} 个")

    # 清空当前圈选
    if st.button("🧹 清空当前打点"):
        st.session_state.draw_points = []
        save_state()
        st.rerun()

    # 保存障碍物（你给的稳定逻辑）
    if st.button("✅ 保存障碍物", type="primary"):
        if len(st.session_state.draw_points) >= 3:
            st.session_state.obstacles.append({
                "name": name,
                "height": height,
                "points": st.session_state.draw_points.copy()
            })
            st.session_state.draw_points = []
            save_state()
            st.success("保存成功！永久显示！")
            st.rerun()
        else:
            st.warning("至少需要3个点")

    st.divider()
    st.subheader("📋 已保存障碍物")
    for i, ob in enumerate(st.session_state.obstacles):
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"📍 {ob['name']} ({ob['height']}m)")
        with col2:
            if st.button("删", key=f"del{i}"):
                del st.session_state.obstacles[i]
                save_state()
                st.rerun()

# ==================== 右侧地图（你给的稳定圈选逻辑） ====================
with col_right:
    st.title("南京科技职业学院 · 无人机地图")

    # 初始化地图
    m = folium.Map(location=[32.2335, 118.7475], zoom_start=17)

    # 绘制已保存障碍物（你给的稳定绘制逻辑）
    for ob in st.session_state.obstacles:
        ps = [[lat, lng] for lng, lat in ob['points']]
        folium.Polygon(
            locations=ps,
            color='red',
            fill=True,
            fill_opacity=0.5
        ).add_to(m)

    # 绘制当前正在圈选的点
    if len(st.session_state.draw_points) >= 1:
        pts = [[lat, lng] for lng, lat in st.session_state.draw_points]
        folium.PolyLine(
            locations=pts,
            color='blue',
            weight=4
        ).add_to(m)

    # 地图交互（你给的稳定打点逻辑）
    o = st_folium.st_folium(m, width=1200, height=680)

    # 核心：地图点击打点（真正稳定！）
    if o and o.get("last_clicked"):
        lat = o["last_clicked"]["lat"]
        lng = o["last_clicked"]["lng"]
        pt = (round(lng,6), round(lat,6))
        
        if pt != st.session_state.last_click:
            st.session_state.last_click = pt
            st.session_state.draw_points.append(pt)
            save_state()  # 实时保存！
            st.rerun()
