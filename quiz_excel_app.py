import streamlit as st
import pandas as pd
import json
from streamlit_local_storage import LocalStorage

st.set_page_config(page_title="化学检验员刷题系统", layout="wide")
ls = LocalStorage()

# ========== 加载浏览器本地保存的答题记录 ==========
def load_record():
    saved = ls.getItem("quiz_answer_record")
    if saved:
        return json.loads(saved)
    return {}

def save_record(rec):
    ls.setItem("quiz_answer_record", json.dumps(rec, ensure_ascii=False))

# 初始化
if "answer_record" not in st.session_state:
    st.session_state.answer_record = load_record()
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0

# ========== 上传题库 ==========
st.title("化学检验员刷题平台")
uploaded_file = st.file_uploader("上传你的题库Excel（xlsx）", type="xlsx")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    total_q = len(df)
    tab1, tab2, tab3 = st.tabs(["📖 刷题页面", "📋 题目预览（查看对错）", "❌ 错题库"])

    # ===================== Tab1：刷题页面 =====================
    with tab1:
        current_idx = st.session_state.current_idx
        if 0 <= current_idx < total_q:
            row = df.iloc[current_idx]
            st.markdown(f"### 第{current_idx+1}题 / {total_q}题 【{row['题型']}】【{row['难度']}】")
            st.markdown(f"**题目：** {row['题目']}")
            st.divider()

            # 收集可用选项（A/B/C/D/E不为空的）
            option_dict = {}
            for opt in ["A","B","C","D","E"]:
                if pd.notna(row[opt]) and str(row[opt]).strip()!="":
                    option_dict[opt] = row[opt]

            correct_ans = str(row["答案"]).strip()
            options_list = [f"{k}. {v}" for k,v in option_dict.items()]

            # 如果这题已经答过，读取上次选择
            default_select = None
            if str(current_idx) in st.session_state.answer_record:
                old_user_ans = st.session_state.answer_record[str(current_idx)]["user_ans"]
                default_select = f"{old_user_ans}. {option_dict[old_user_ans]}"

            user_select = st.radio("请选择答案", options_list, index=options_list.index(default_select) if default_select else None)

            col_submit, col_prev, col_next = st.columns([2,1,1])
            with col_submit:
                submit_btn = st.button("提交答案")
            with col_prev:
                prev_btn = st.button("上一题")
            with col_next:
                next_btn = st.button("下一题")

            # 提交答案逻辑
            if submit_btn and user_select:
                user_ans = user_select.split(".")[0]
                is_correct = user_ans == correct_ans
                # 存记录，key转字符串，json不能用数字key
                st.session_state.answer_record[str(current_idx)] = {
                    "user_ans": user_ans,
                    "is_correct": is_correct
                }
                save_record(st.session_state.answer_record) # 保存到浏览器localStorage
                if is_correct:
                    st.success(f"✅回答正确！正确答案：{correct_ans}")
                else:
                    st.error(f"❌回答错误！正确答案：{correct_ans}")
                st.markdown(f"解析：{row['解析']}")

            # 上一题、下一题
            if prev_btn:
                st.session_state.current_idx = max(0, current_idx -1)
                st.rerun()
            if next_btn:
                st.session_state.current_idx = min(total_q-1, current_idx +1)
                st.rerun()
        else:
            st.info("题库加载完成，可以开始刷题！")

    # ===================== Tab2：题目预览（全部题目，标记对错） =====================
    with tab2:
        st.subheader("📋 全部题目预览（点击题号跳转）")
        st.markdown("🔘未作答 | ✅答对 | ❌答错")
        col_num = st.columns(10) # 一行放10个题号按钮
        for q_idx in range(total_q):
            status = "🔘"
            if str(q_idx) in st.session_state.answer_record:
                if st.session_state.answer_record[str(q_idx)]["is_correct"]:
                    status = "✅"
                else:
                    status = "❌"
            # 按列循环放按钮
            with col_num[q_idx %10]:
                if st.button(f"{q_idx+1}{status}", key=f"preview_btn_{q_idx}"):
                    st.session_state.current_idx = q_idx
                    st.rerun()
        st.divider()
        # 统计
        answered = len(st.session_state.answer_record)
        right_count = sum(1 for rec in st.session_state.answer_record.values() if rec["is_correct"])
        wrong_count = answered - right_count
        st.write(f"答题统计：已答 {answered}/{total_q}｜✅答对：{right_count}｜❌答错：{wrong_count}")
        if answered>0:
            st.write(f"正确率：{right_count/answered*100:.1f}%")

    # ===================== Tab3：错题库（只显示答错的题目） =====================
    with tab3:
        st.subheader("❌ 错题本（只显示做错的题目）")
        wrong_index_list = [int(q_idx) for q_idx, rec in st.session_state.answer_record.items() if not rec["is_correct"]]
        if len(wrong_index_list)==0:
            st.success("🎉 目前还没有错题！继续加油！")
        else:
            st.write(f"一共有 {len(wrong_index_list)} 道错题：")
            col_wrong = st.columns(8)
            for i, q_idx in enumerate(wrong_index_list):
                with col_wrong[i%8]:
                    if st.button(f"{q_idx+1}", key=f"wrong_btn_{q_idx}"):
                        st.session_state.current_idx = q_idx
                        st.rerun()
            st.divider()
            st.markdown("点击错题题号，自动跳转到刷题页面重做")

else:
    st.info("⬆️ 请上传Excel题库文件")

# 侧边栏操作
with st.sidebar:
    st.header("系统操作")
    if st.button("🔄清空所有答题记录"):
        st.session_state.answer_record = {}
        save_record({})
        st.session_state.current_idx = 0
        st.rerun()
    st.info("记录保存在你的浏览器本地，关闭网页重新打开不会丢失；清除浏览器缓存会清空记录。")