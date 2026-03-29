# 无人机通信“心跳”监测可视化
基于 Python + Streamlit 实现无人机心跳包模拟、断线检测、实时数据可视化，并部署至 Streamlit Cloud。

## 📋 项目需求与目标
### 需求拆解
- 心跳包模拟：每秒发送带序号和时间戳的心跳数据
- 断线检测：超过3秒未收到心跳包，立即触发断线报警
- 数据可视化：以折线图实时展示心跳包发送时序
- 云端部署：系统部署云端，支持公网访问与演示

### 项目目标
- 核心目标：构建功能完整、界面友好的无人机通信监测系统
- 技术目标：熟练运用 Python、Streamlit 技术栈，掌握云端部署
- 学习目标：理解网络通信原理、多线程编程及数据可视化

## 🛠️ 技术栈选型
- 核心开发：Python
- 可视化界面：Streamlit
- 数据处理：Pandas、Plotly
- 版本控制：GitHub
- 云端部署：Streamlit Cloud

## 📁 代码结构展示
```
drone-heartbeat-monitor/
├── app.py              # 主程序，核心逻辑与界面
├── requirements.txt    # 项目依赖包列表
└── README.md           # 项目说明与部署指南
```

## 🚀 本地运行步骤
1. 环境准备：安装 Python 3.8+
2. 安装依赖
```bash
pip install -r requirements.txt
```
3. 启动程序
```bash
streamlit run app.py
```
4. 浏览器打开本地地址即可使用

## 🌐 云端部署链接
Streamlit Cloud 部署地址：  
https://app-data-visual-lmpf5rr8dafykqyi6nnffr.streamlit.app/

## ⚠️ 问题与解决
1. **多线程同步问题**  
现象：快速启停时数据错乱、程序崩溃  
解决：使用 Streamlit session_state 管理全局变量，确保线程安全

2. **部署依赖包版本冲突**  
现象：Streamlit Cloud 部署失败、应用无法启动  
解决：在 requirements.txt 明确指定依赖包版本

3. **可视化图表实时更新卡顿**  
现象：数据量大时图表更新卡顿  
解决：优化更新逻辑，限制图表显示数据量

## 📌 项目总结
- 成功完成无人机心跳监测系统开发、部署与演示
- 实现心跳模拟、断线检测、数据可视化、云端部署全功能
- 掌握 GitHub 托管、Streamlit Cloud 部署全流程

---

