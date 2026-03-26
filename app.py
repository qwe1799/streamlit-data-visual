# 导入必要库
import streamlit as st
import pandas as pd
import numpy as np

# 设置页面标题
st.title('GitHub + Streamlit 数据可视化示例')

# 生成模拟数据（也可读取本地/在线CSV、Excel等）
data = pd.DataFrame(
    np.random.randn(50, 3),  # 50行3列的随机数
    columns=['A列', 'B列', 'C列']
)

# Streamlit可视化：折线图（一行代码即可渲染）
st.subheader('随机数据折线图')
st.line_chart(data)

# 额外展示原始数据（可选）
st.subheader('原始数据预览')
st.dataframe(data.head(10))
