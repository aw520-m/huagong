import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="化学检验员刷题系统", layout="wide")

# ========== 初始化会话状态 ==========
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "answer_record" not in st.session_state:
    st.session_state.answer_record = {}

# ========== 上传题库 ==========
st.title("化学检验员刷题平台")
uploaded_file = st.file_uploader("上传你的题库Excel（xlsx）", type="xlsx")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    total_q = len(df)
    # 自动适配Excel里的列名，避免KeyError
    has_type = "题型" in df.columns
    has_diff = "难度" in df.columns
    has_analysis = "解析" in df.columns
    has_option_E = "E" in df.columns

    tab1, tab2, tab3 = st.tabs(["📖 刷题页面", "📋 题目预览（查看对错）", "❌ 错题库"])

    # ===================== Tab1：刷题页面 =====================
    with tab1:
        current_idx = st.session_state.current_idx
        if 0 <= current_idx < total_q:
            row = df.iloc[current_idx]
            # 兼容无题型/难度列
            type_text = f"【{row['题型']}】" if has_type else ""
            diff_text = f"【{row['难度']}】" if has_diff else ""
            st.markdown(f"### 第{current_idx+1}题 / {total_q}题 {type_text} {diff_text}")
            st.markdown(f"**题目：** {row['题目']}")
            st.divider()

            # 自动读取存在的选项，兼容无E列/空选项
            option_dict = {}
            for opt in ["A","B","C","D","E"]:
                if opt == "E" and not has_option_E:
                    continue
                if pd.notna(row[opt]) and str(row[opt]).strip()!="":
                    option_dict[opt] = row[opt]

            correct_ans = str(row["答案"]).strip()
            options_list = [f"{k}. {v}" for k,v in option_dict.items()]

            # 读取历史选择
            default_select = None
            if current_idx in st.session_state.answer_record:
                old_user_ans = st.session_state.answer_record[current_idx]["user_ans"]
                if old_user_ans in option_dict:
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
                st.session_state.answer_record[current_idx] = {
                    "user_ans": user_ans,
                    "is_correct": is_correct
                }
                if is_correct:
                    st.success(f"✅回答正确！正确答案：{correct_ans}")
                else:
                    st.error(f"❌回答错误！正确答案：{correct_ans}")
                # 兼容无解析列，有解析才显示
                if has_analysis and pd.notna(row["解析"]):
                    st.markdown(f"**解析：** {row['解析']}")

            # 上一题/下一题
            if prev_btn:
                st.session_state.current_idx = max(0, current_idx -1)
                st.rerun()
            if next_btn:
                st.session_state.current_idx = min(total_q-1, current_idx +1)
                st.rerun()
        else:
            st.info("题库加载完成，可以开始刷题！")

    # ===================== Tab2：题目预览 =====================
    with tab2:
        st.subheader("📋 全部题目预览（点击题号跳转）")
        st.markdown("🔘未作答 | ✅答对 | ❌答错")
        col_num = st.columns(10)
        for q_idx in range(total_q):
            status = "🔘"
            if q_idx in st.session_state.answer_record:
                if st.session_state.answer_record[q_idx]["is_correct"]:
                    status = "✅"
                else:
                    status = "❌"
            with col_num[q_idx %10]:
                if st.button(f"{q_idx+1}{status}", key=f"preview_btn_{q_idx}"):
                    st.session_state.current_idx = q_idx
                    st.rerun()
        st.divider()
        # 答题统计
        answered = len(st.session_state.answer_record)
        right_count = sum(1 for rec in st.session_state.answer_record.values() if rec["is_correct"])
        wrong_count = answered - right_count
        st.write(f"答题统计：已答 {answered}/{total_q}｜✅答对：{right_count}｜❌答错：{wrong_count}")
        if answered>0:
            st.write(f"正确率：{right_count/answered*100:.1f}%")

    # ===================== Tab3：错题库 =====================
    with tab3:
        st.subheader("❌ 错题本（只显示做错的题目）")
        wrong_index_list = [q_idx for q_idx, rec in st.session_state.answer_record.items() if not rec["is_correct"]]
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

# 侧边栏：答题记录管理
with st.sidebar:
    st.header("答题记录管理")
    # 导出记录
    json_str = json.dumps(st.session_state.answer_record, ensure_ascii=False, indent=2)
    st.download_button("💾下载答题记录(json)", json_str, file_name="quiz_record.json", mime="application/json")
    # 导入记录
    record_file = st.file_uploader("📂上传答题记录json恢复", type="json")
    if record_file is not None:
        load_data = json.load(record_file)
        st.session_state.answer_record = load_data
        st.success("✅记录加载成功！")
        st.rerun()
    if st.button("🔄清空所有答题记录"):
        st.session_state.answer_record = {}
        st.session_state.current_idx = 0
        st.rerun()