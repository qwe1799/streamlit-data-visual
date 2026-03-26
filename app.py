import streamlit as st
import pandas as pd
import time
import datetime

st.title("无人机通信心跳监测可视化")

# 初始化数据
if "heartbeat_data" not in st.session_state:
    st.session_state.heartbeat_data = []
    st.session_state.seq = 0
    st.session_state.last_receive_time = time.time()

# 模拟心跳与掉线检测
def simulate_heartbeat():
    st.session_state.seq += 1
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.last_receive_time = time.time()
    st.session_state.heartbeat_data.append({
        "seq": st.session_state.seq,
        "time": current_time,
        "status": "received"
    })

def check_timeout():
    current_time = time.time()
    if current_time - st.session_state.last_receive_time > 3:
        st.session_state.heartbeat_data.append({
            "seq": st.session_state.seq,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "timeout"
        })
        st.warning("⚠️ 连接超时！3秒未收到心跳包！")

# 定时更新数据
if st.button("开始监测"):
    while True:
        simulate_heartbeat()
        check_timeout()
        df = pd.DataFrame(st.session_state.heartbeat_data)
        st.subheader("心跳包时序图")
        st.line_chart(df, x="time", y="seq", color="status")
        st.subheader("原始数据")
        st.dataframe(df)
        time.sleep(1)
