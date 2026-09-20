import streamlit as st
import pandas as pd

# 网页基础配置
st.set_page_config(page_title="Excel刷题工具", page_icon="📝", layout="wide")
st.title("📝 网页刷题工具（Excel导入版）")
st.divider()

# 初始化会话状态（保存做题进度，刷新页面不丢失）
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "user_answer" not in st.session_state:
    st.session_state.user_answer = ""

# 1. 上传Excel题库
uploaded_file = st.file_uploader("📤 上传Excel题库文件", type=["xlsx", "xls"])

if uploaded_file:
    # 2. 读取Excel文件
    try:
        df = pd.read_excel(uploaded_file)
        # 校验必要列
        required_cols = {"题目", "答案"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            st.error(f"Excel缺少必要列：{missing_cols}，请检查表头（必须包含「题目」「答案」）")
            st.stop()
    except Exception as e:
        st.error(f"文件读取失败：{e}")
        st.stop()

    # 3. 核心数据初始化
    total_questions = len(df)
    current_idx = st.session_state.current_index
    # 防止题号越界
    current_idx = max(0, min(current_idx, total_questions - 1))
    st.session_state.current_index = current_idx

    # 4. 展示题目信息
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("当前题号", f"{current_idx + 1} / {total_questions}")
    with col2:
        # 题型标签：判断题/单选题/问答题
        if "题型" in df.columns:
            question_type = df.iloc[current_idx]["题型"]
            st.success(f"题型：{question_type}")

    st.divider()

    # 5. 展示题目内容
    current_question = df.iloc[current_idx]["题目"]
    st.markdown(f"### 题目：{current_question}")

    # 6. 选择题选项展示（兼容无选项的问答题）
    option_cols = ["A", "B", "C", "D", "E", "F"]
    has_options = any(col in df.columns for col in option_cols)
    if has_options:
        st.markdown("**选项：**")
        for col in option_cols:
            if col in df.columns:
                option_content = df.iloc[current_idx][col]
                if pd.notna(option_content):
                    st.write(f"{col}. {option_content}")

    st.divider()

    # 7. 答题&查看答案区域
    tab1, tab2 = st.tabs(["✍️ 答题区", "👀 答案解析"])
    with tab1:
        # 选择题用单选框，问答题用输入框
        if has_options:
            user_answer = st.radio("你的答案", options=option_cols, key="user_answer")
        else:
            user_answer = st.text_input("你的答案", key="user_answer")

        # 提交判断
        if st.button("提交答案", type="primary"):
            correct_answer = str(df.iloc[current_idx]["答案"]).strip()
            user_answer_str = str(user_answer).strip()
            if user_answer_str == correct_answer:
                st.success("✅ 回答正确！")
            else:
                st.error(f"❌ 回答错误，正确答案是：{correct_answer}")

    with tab2:
        # 查看答案和解析
        correct_answer = df.iloc[current_idx]["答案"]
        st.info(f"**正确答案：{correct_answer}**")
        if "解析" in df.columns:
            analysis = df.iloc[current_idx]["解析"]
            if pd.notna(analysis):
                st.markdown(f"**解析：**\n{analysis}")

    st.divider()

    # 8. 题号切换按钮
    col_prev, col_next, col_reset = st.columns([1, 1, 1])
    with col_prev:
        if st.button("⬅️ 上一题", disabled=(current_idx == 0)):
            st.session_state.current_index -= 1
            st.rerun()
    with col_next:
        if st.button("➡️ 下一题", disabled=(current_idx == total_questions - 1), type="primary"):
            st.session_state.current_index += 1
            st.rerun()
    with col_reset:
        if st.button("🔄 重置进度"):
            st.session_state.current_index = 0
            st.rerun()

else:
    # 未上传文件时的引导
    st.info("👈 请上传Excel题库文件，格式要求如下：")
    st.markdown("""
    ### Excel题库格式规范
    1. 第一行必须是表头，至少包含 **「题目」** 和 **「答案」** 两列
    2. 可选列：「题型」「A」「B」「C」「D」「解析」（用于选择题和答案讲解）
    """)
    # 示例Excel预览
    st.markdown("### 示例题库内容")
    sample_df = pd.DataFrame({
        "题型": ["单选题", "判断题", "问答题"],
        "题目": ["Python中用于输出内容的函数是？", "Python中变量名可以以数字开头", "简述Python中def的作用"],
        "A": ["print", "正确", ""],
        "B": ["input", "错误", ""],
        "C": ["len", "", ""],
        "D": ["type", "", ""],
        "答案": ["A", "B", "定义函数"],
        "解析": ["print()函数用于控制台输出内容", "变量名不能以数字开头", "def关键字用于定义自定义函数"]
    })
    st.dataframe(sample_df, use_container_width=True)