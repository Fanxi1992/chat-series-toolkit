import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
# import pinecone
from p_version_module_pinecone_doc_name import get_doc_names
from p_version_module_process_new_papers import process_files
from p_version_module_return_call_chunks import return_chunks
from tempfile import NamedTemporaryFile
import re
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.altex import scatter_chart
from annotated_text import annotated_text
from annotated_text import annotated_text, annotation
from streamlit_extras.app_logo import add_logo
from streamlit_extras.badges import badge
from streamlit_extras.bottom_container import bottom
from streamlit_extras.chart_annotations import get_annotations_chart
import pandas as pd
from streamlit_extras.chart_container import chart_container
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from streamlit_extras.colored_header import colored_header
from streamlit_extras.customize_running import center_running
import time
from streamlit_extras.dataframe_explorer import dataframe_explorer
from streamlit_extras.echo_expander import echo_expander
from streamlit_extras.grid import grid
from streamlit_extras.keyboard_url import keyboard_to_url
from streamlit_extras.let_it_rain import rain
from streamlit_extras.mention import mention
import streamlit as st
from streamlit_extras.stateful_chat import chat
from streamlit_extras.stodo import to_do
import random
from streamlit_extras.switch_page_button import switch_page
import dotenv
dotenv.load_dotenv()


# 设置页面配置为全屏布局
st.set_page_config(page_title='Academic Toolkits', layout="wide")

# 正则化
def normalize_filename(filename):
    # 使用正则表达式匹配文件名中的最后一部分
    match = re.search(r'[^\\/"<>|\r\n]+\.pdf$', filename)
    if match:
        return match.group()
    else:
        return filename


@st.cache_resource
def create_QA_chain():
    # gpt-3.5-turbo-0125  gpt-4-1106-preview
    model = ChatOpenAI(
        model='gpt-4-turbo-2024-04-09',
        temperature=0.2,
        streaming=True,
        openai_api_base="https://api.gptsapi.net/v1"
    )

    full_template = """you are a professional academic paper analysis assistant named SF_bot. You are very good at summarizing and extracting the content of literature, as well as finding the key points of knowledge in literature, and providing professional, logical, and well-organized answers based on your own knowledge base. You will answer the user's question based on the following context. You always reply in Chinese.

    Context: {full_context}

    Question: {question}
    """

    full_prompt = ChatPromptTemplate.from_template(full_template)
    full_chain = (
            {"full_context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | full_prompt
            | model
            | StrOutputParser()
    )
    return full_chain


def get_pinecone_connection():
    # 获取每个人的上传文献的文件名称列表
    panjiao_docs = get_doc_names("panjiao")


    return [panjiao_docs]


def get_response(chain, user_query, full_context):
    try:
        input_data = {
            "full_context": full_context,
            "question": user_query,
        }
        return chain.stream(input_data)
    except Exception as e:
        error_message = f"发生错误: {str(e)}"
        return {"error": error_message}


# 获得所有人的文件名称列表，下面根据下拉框来确定是谁，并赋值给initial_list
if 'db_initialized' not in st.session_state:
    st.session_state['ids_doc_names'] = get_pinecone_connection()
    st.session_state['db_initialized'] = True


QA_chain = create_QA_chain()

# 以下是一个示例用法，假设你需要使用 ids_doc_names 进行一些操作
if 'ids_doc_names' in st.session_state:
    ids_doc_names = st.session_state['ids_doc_names']


# st.header("贾建民课题组文献综述分析系统")
# 创建宽度比为 2.5:1 的两列
col1, col2 = st.columns([2.5, 1])


with col2:
    colored_header(
        label="文件选择和参数配置",
        description="",
        color_name="blue-70",
    )

    # 选择身份
    ids = ["潘娇"]
    index_names = ["panjiao"]
    radio_btn_id = st.radio("选择身份", ids, index=0, key="radio1")
    index_id = ids.index(radio_btn_id)
    person_docs_name = list(ids_doc_names[index_id])
    index_name = index_names[index_id]

    st.session_state.pdf_list = []
    # 如果"last_id"不存在，或者当前的身份与"last_id"不同，那么就重新设置pdf_list2
    if "last_id" not in st.session_state or st.session_state["last_id"] != radio_btn_id:
        # 检查是否已经为这个身份保存了文件列表
        if f"pdf_list2_{radio_btn_id}" in st.session_state:
            # 如果已经保存了文件列表，就加载这个文件列表
            st.session_state.pdf_list2 = st.session_state[f"pdf_list2_{radio_btn_id}"]
        else:
            # 如果没有保存文件列表，就初始化文件列表
            st.session_state.pdf_list2 = person_docs_name
            st.session_state[f"pdf_list2_{radio_btn_id}"] = person_docs_name
        st.session_state["last_id"] = radio_btn_id

    # 这一步非常重要，确保状态在组件实例化之前就已初始化
    for filename in st.session_state.pdf_list2:
        if f"checked_{filename}" not in st.session_state:
            # 初始化状态为未勾选
            st.session_state[f"checked_{filename}"] = True


    # 定义是针对每个文件单独提问，还是针对所有勾选文件进行提问
    radio_btn = st.radio("是否需要返回原始文本", ["需要", "不需要"], index=0, key="radio")

    # 大模型的温度选择，返回重排序之后的chunks
    chunks_num = st.slider("检索返回文本数量（每段文本约350words）", min_value=2, max_value=8, value=5, step=1, key="slider2")

    uploaded_files = st.file_uploader("上传文献（可批量）", type=["pdf"], accept_multiple_files=True)
    # 如果有文件上传，将文件名添加到pdf_list2后开始向量化并加上进度条
    if uploaded_files:
        # if st.button("Submit & Process"):
        with st.spinner("正在处理并向量化文献..."):
            for uploaded_file in uploaded_files:
                # 获取上传文件的文件名
                filename = uploaded_file.name
                with NamedTemporaryFile(delete=False, suffix=".pdf",prefix=filename) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                # 对文件进行向量化并上传，更新进度条
                new_papers_name = process_files(tmp_file_path,index_name)
                print('新向量化的文件名为：',new_papers_name)
                if new_papers_name == "解析文章并向量化失败,请重启网页后重新上传":
                    st.error("this is an error,请重启！！")
                else:
                    # 如果文件名还不在pdf_list2中
                    if new_papers_name not in st.session_state.pdf_list2:
                        # 将文件名添加到pdf_list2
                        st.session_state.pdf_list2.append(new_papers_name)
                        # 初始化checkbox状态
                        st.session_state[f"checked_{new_papers_name}"] = True
                        st.success("文献处理完成！")
                    if new_papers_name not in st.session_state[f"pdf_list2_{radio_btn_id}"]:
                        st.session_state[f"pdf_list2_{radio_btn_id}"].append(new_papers_name)


    # 显示当前的PDF文件名和对应的checkbox
    st.write("请选择要用于文献综述分析的文献:")

    # 确保不会直接修改Session State中的状态
    # 而是通过用户勾选状态来更新pdf_list
    for filename in st.session_state.pdf_list2:
        # 正则化文件名
        # show_filename = normalize_filename(filename)

        checkbox_checked = st.checkbox(f"{filename}", key=f"checked_{filename}")

        # 更新pdf_list，根据checkbox的状态进行添加或删除
        if checkbox_checked:
            # 如果勾选，并且pdf_list中没有这个文件名
            if filename not in st.session_state.pdf_list:
                st.session_state.pdf_list.append(filename)
        else:
            # 如果未勾选，并且pdf_list中有这个文件名
            if filename in st.session_state.pdf_list:
                st.session_state.pdf_list.remove(filename)

    print("激活检索状态的pdf_list:", st.session_state.pdf_list)
    print("全部可用的pdf_list2:", st.session_state.pdf_list2)
    # st.session_state.pdf_list 是用来遴选知识库里的vector的，只对这些metadata在pdf_list里的vector进行操作






with col1:
    col3, col4 = st.columns([4, 1])
    with col3:
        colored_header(
            label="我的文献分析工具v1.0",
            description="",
            color_name="violet-70",
        )
    with col4:
        badge(type="github", name="streamlit/streamlit")
        badge(type="twitter", name="Joy2022art")



    # 渲染全部对话记录
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content="你好，我是你的文献综述助手，有什么问题可以帮助你的吗？"),
        ]

    # 设置一个按钮，用于清空除了第一条消息之外的所有消息
    if st.button(label="清空对话记录",type="primary"):
        st.session_state.chat_history = st.session_state.chat_history[:1]



    # conversation
    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.write(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.write(message.content)


    # user input
    user_query = st.chat_input("Type your message here...")
    if user_query is not None and user_query != "":
        st.session_state.chat_history.append(HumanMessage(content=user_query))

        with st.chat_message("Human"):
            st.markdown(user_query)

        with st.chat_message("AI"):
            full_context = return_chunks(user_input=user_query,index=index_name ,top_k=(st.session_state.slider2)*2, rerank_top_k=st.session_state.slider2,filter_source=st.session_state.pdf_list)
            response = st.write_stream(get_response(QA_chain,user_query,full_context))
            if st.session_state.radio == "需要":
                st.write(full_context)
                response = response + "\n\n" + full_context
            else:
                pass
        st.session_state.chat_history.append(AIMessage(content=response))













