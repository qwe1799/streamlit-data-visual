# 无人机通信心跳监测可视化
基于 Python + Streamlit 实现无人机心跳包模拟、掉线检测及数据可视化，并部署至 Streamlit Cloud。

## 📋 任务介绍
本项目为分组作业，核心任务如下：
1. **模拟心跳包**：用 Python 程序模拟无人机每秒发送一个包含序号和时间的心跳包；
2. **掉线检测**：地面站接收心跳包，若 3 秒未收到则触发连接超时报警；
3. **数据可视化**：通过 Streamlit 制作网页，以折线图展示心跳包序号随时间的变化；
4. **部署提交**：将代码上传至 GitHub，并部署到 Streamlit Cloud，提交部署链接及项目PPT。

## 🛠️ 技术栈
- 核心语言：Python
- 可视化框架：Streamlit
- 代码托管：GitHub
- 在线部署：Streamlit Cloud

## 🚀 本地运行步骤
### 1. 环境准备
确保已安装 Python 环境，推荐版本 3.8+。

### 2. 安装依赖
克隆本仓库后，在项目根目录执行以下命令安装依赖：
```bash
pip install -r requirements.txt
