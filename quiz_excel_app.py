import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="刷题系统", layout="wide")

# ========== 初始化会话状态 ==========
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "answer_record" not in st.session_state:
    st.session_state.answer_record = {}

# ========== 上传题库 ==========
st.title("刷题平台")
uploaded_file = st.file_uploader("上传你的题库Excel（xlsx）", type="xlsx")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    total_q = len(df)
    # 检测存在哪些列
    has_type = "题型" in df.columns
    has_diff = "难度" in df.columns
    has_analysis = "解析" in df.columns
    has_E = "E" in df.columns

    tab1, tab2, tab3 = st.tabs(["📖 刷题页面", "📋 题目预览", "❌ 错题库"])

    # ========== Tab1 刷题页面 ==========
    with tab1:
        current_idx = st.session_state.current_idx
        if 0 <= current_idx < total_q:
            row = df.iloc[current_idx]
            type_text = f"【{row['题型']}】" if has_type else "【单选】"
            diff_text = f"【{row['难度']}】" if has_diff else ""
            st.markdown(f"### 第{current_idx+1}题 / {total_q}题 {type_text}{diff_text}")
            st.markdown(f"**{row['题目']}**")
            st.divider()

            # 读取选项
            option_dict = {}
            for opt in ["A", "B", "C", "D", "E"]:
                if opt == "E" and not has_E:
                    continue
                cell_val = row[opt]
                if pd.notna(cell_val) and str(cell_val).strip() != "":
                    option_dict[opt] = str(cell_val).strip()

            # 处理正确答案
            correct_ans_raw = str(row["答案"]).strip()
            correct_ans_list = [x.strip() for x in correct_ans_raw.split(",")]
            is_multi = (len(correct_ans_list) > 1)  # 多个答案=多选题

            option_list = [f"{k}. {v}" for k, v in option_dict.items()]

            # 读取历史作答
            default_val = None
            if current_idx in st.session_state.answer_record:
                old_ans = st.session_state.answer_record[current_idx]["user_ans"]
                if isinstance(old_ans, list):
                    default_val = [f"{k}. {option_dict[k]}" for k in old_ans if k in option_dict]
                else:
                    if old_ans in option_dict:
                        default_val = f"{old_ans}. {option_dict[old_ans]}"

            # 区分单选/多选组件
            if is_multi:
                st.info("✅ 本题为多选题，请选择全部正确答案")
                user_choose = st.multiselect("请选择答案", option_list, default=default_val)
            else:
                user_choose = st.radio("请选择答案", option_list, index=option_list.index(default_val) if default_val else None)

            col_submit, col_prev, col_next = st.columns([2, 1, 1])
            with col_submit:
                submit_btn = st.button("提交答案")
            with col_prev:
                prev_btn = st.button("上一题")
            with col_next:
                next_btn = st.button("下一题")

            if submit_btn and user_choose:
                # 解析用户选择
                if is_multi:
                    user_ans = [item.split(".")[0].strip() for item in user_choose]
                else:
                    user_ans = user_choose.split(".")[0].strip()

                # 判断是否答对
                if is_multi:
                    # 多选题：必须完全一致，顺序无关
                    is_right = set(user_ans) == set(correct_ans_list)
                else:
                    is_right = user_ans == correct_ans_list[0]

                st.session_state.answer_record[current_idx] = {
                    "user_ans": user_ans,
                    "is_correct": is_right
                }

                # 输出结果
                if is_right:
                    st.success(f"✅回答正确！正确答案：{correct_ans_raw}")
                else:
                    st.error(f"❌回答错误！正确答案：{correct_ans_raw}")

                # 显示解析
                if has_analysis and pd.notna(row["解析"]):
                    st.markdown(f"**解析：** {row['解析']}")

            if prev_btn:
                st.session_state.current_idx = max(0, current_idx - 1)
                st.rerun()
            if next_btn:
                st.session_state.current_idx = min(total_q - 1, current_idx + 1)
                st.rerun()

    # ========== Tab2 题目预览 ==========
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
            with col_num[q_idx % 10]:
                if st.button(f"{q_idx+1}{status}", key=f"prev_{q_idx}"):
                    st.session_state.current_idx = q_idx
                    st.rerun()
        st.divider()
        answered = len(st.session_state.answer_record)
        right_cnt = sum(1 for rec in st.session_state.answer_record.values() if rec["is_correct"])
        wrong_cnt = answered - right_cnt
        st.write(f"已答：{answered}/{total_q}｜✅答对 {right_cnt}｜❌答错 {wrong_cnt}")
        if answered > 0:
            st.write(f"正确率：{right_cnt / answered *100:.1f}%")

    # ========== Tab3 错题库 ==========
    with tab3:
        st.subheader("❌ 错题本")
        wrong_list = [idx for idx, rec in st.session_state.answer_record.items() if not rec["is_correct"]]
        if len(wrong_list) == 0:
            st.success("🎉 暂无错题！")
        else:
            st.write(f"错题数量：{len(wrong_list)}")
            cols_wrong = st.columns(8)
            for i, q_idx in enumerate(wrong_list):
                with cols_wrong[i % 8]:
                    if st.button(f"{q_idx+1}", key=f"wrong_{q_idx}"):
                        st.session_state.current_idx = q_idx
                        st.rerun()
            st.divider()
            st.markdown("点击错题题号，直接跳转到对应题目重做")

else:
    st.info("⬆️ 上传你的Excel题库文件")

# ========== 侧边栏 记录管理 ==========
with st.sidebar:
    st.header("答题记录管理")
    json_str = json.dumps(st.session_state.answer_record, ensure_ascii=False, indent=2)
    st.download_button("💾下载答题记录(json)", json_str, file_name="quiz_record.json", mime="application/json")

    record_file = st.file_uploader("📂上传答题记录json恢复", type="json", accept_multiple_files=False)
    if record_file is not None:
        load_data = json.load(record_file)
        st.session_state.answer_record = load_data
        st.success("✅记录加载成功！")
        st.rerun()

    if st.button("🔄清空所有答题记录"):
        st.session_state.answer_record = {}
        st.session_state.current_idx = 0
        st.rerun()