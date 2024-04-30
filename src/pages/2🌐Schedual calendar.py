
from streamlit_extras.stateful_chat import chat
from streamlit_extras.stodo import to_do
import random
from streamlit_extras.switch_page_button import switch_page

#
# # 定义自定义 emoji 列表
# custom_emojis = [
#     "😀", "😎", "😊", "🥳", "😍", "🚀", "🎉", "🌟",
#     "😂", "😭", "🤣", "😢", "😡", "🥰", "😘", "🤩",
#     "🤔", "😴", "🥺", "😮", "👍", "👎", "🔥", "🌈",
#     "🎄", "🎃", "👻", "🐱", "🦊", "🐼"
# ]
#
#
# # 获取用户输入
# user_input = st.text_input("输入今日任务", "Type here...")
# # 加一个按钮
# submit = st.button("Submit")
#
#
# # 生成随机的自定义 emoji
# random_emoji = random.choice(custom_emojis)
#
# # 如果用户输入非空，则在用户输入文本前添加随机 emoji
# if submit and user_input.strip():
#     result = f"{random_emoji} {user_input}"
#     to_do(
#         [(st.write, result)],
#         "coffee",
#     )
#
#
#
# to_do(
#     [(st.write, "🥞 Have a nice breakfast")],
#     "pancakes",
# )
# to_do(
#     [(st.write, ":train: Go to work!")],
#     "work",
# )
#
#








import streamlit as st
import random
import time


now = time.time()

time = str(now)


# 定义自定义 emoji 列表
custom_emojis = [
    "😀", "😎", "😊", "🥳", "😍", "🚀", "🎉", "🌟",
    "😂", "😭", "🤣", "😢", "😡", "🥰", "😘", "🤩",
    "🤔", "😴", "🥺", "😮", "👍", "👎", "🔥", "🌈",
    "🎄", "🎃", "👻", "🐱", "🦊", "🐼"
]

# 初始化任务列表
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

# 获取用户输入
user_input = st.text_input("输入今日任务", "Type here...")
submit = st.button("Submit")

# 处理提交
if submit and user_input.strip():
    random_emoji = random.choice(custom_emojis)
    new_task = f"{random_emoji} {user_input}"
    st.session_state.tasks.append(new_task)  # 添加新任务

# 显示任务和删除按钮
for i, task in enumerate(list(st.session_state.tasks)):  # 使用列表复制避免在循环中修改列表
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        to_do([(st.write, task)], f"task_{i}")
    with col2:
        if st.button("删除", key=f"delete_{i}"):
            st.session_state.tasks.remove(task)  # 从列表中删除任务







