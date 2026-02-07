import streamlit as st
import google.generativeai as genai

# 1. 页面配置
st.set_page_config(page_title="Scent Curator Assistant", layout="centered")
st.title("🏯 东方香礼跨境营销助手 (专业版)")

# 2. 初始化对话记忆 (Multi-turn Chat)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. 读取知识库 (增加缓存提高性能)
@st.cache_data
def load_docs():
    try:
        with open("docs/SOP_Flow.md", "r", encoding="utf-8") as f:
            sop = f.read()
        with open("docs/Product_Info.md", "r", encoding="utf-8") as f:
            product = f.read()
        return sop, product
    except Exception as e:
        st.error(f"读取文件失败: {e}")
        return "", ""

sop_content, product_content = load_docs()

# 4. 配置 Gemini API
gemini_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_key:
    st.error("请在 Streamlit Secrets 中配置 GEMINI_API_KEY")
else:
    genai.configure(api_key=gemini_key)

    # 自动选择最合适的 Gemini 模型名称 (修复404问题)
    try:
        available_models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
        model = genai.GenerativeModel(model_name=target_model)
    except Exception as e:
        st.error(f"模型加载失败: {e}")
        model = None

    # 5. 侧边栏控制
    with st.sidebar:
        st.header("控制面板")
        if st.button("清除对话记录"):
            st.session_state.messages = []
            st.rerun()
        st.markdown("---")
        st.info("💡 系统已加载 SOP 与产品手册，现在拥有上下文记忆。")

    # 6. 显示历史聊天记录
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 7. 用户输入逻辑
    if prompt_input := st.chat_input("粘贴客户的话..."):
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt_input)
        st.session_state.messages.append({"role": "user", "content": prompt_input})

        # 8. 核心 Prompt 整合
        # 療癒師角色、望聞問切、破冰追問、轉化意圖
        system_instruction = f"""
        You are a "Scent Healing Mentor" (Eastern Scent Therapist). Your goal is not to sell, but to "diagnose and cure" through scents, building a deep bond with the customer.

        【Knowledge Base】
        SOP: {sop_content}
        Products: {product_content}

        【Instructions for Professionalism & Conversion】
        1. THE SKEPTIC'S GUIDE: If a customer is skeptical, explain the "Transdermal Absorption" and "Olfactory Neural Response" in a sophisticated way (Botanical energy interacting with body heat).
        2. VASCULAR & NERVOUS FOCUS (望聞問切): When symptoms are mentioned, DO NOT jump to products. First, generate 1-2 caring follow-up questions to understand their lifestyle (e.g., stress levels, sleep patterns, or pain triggers).
        3. ANTI-CHAT-END: Every reply must end with a gentle question or an emotional hook to keep the conversation alive.
        4. ROLE: You are an expert friend. Use "I've seen similar cases...", "In our tradition, we believe...", "Actually, your body is telling you...".

        【Output Structure】
        ### 1. 療癒師內部診斷 (Internal Strategy)
        - **SOP 階段**: [目前處於SOP哪一環]
        - **望聞問切 (The Diagnosis)**: [分析症狀背後的成因，並給出1-2個進一步詢問客戶的點]
        - **破冰與追問策略**: [如果客戶這條沒回，你明天該如何用什麼話題重新擊中他的痛點？]

        ### 2. 建議英文回覆 (The Scent Mentor's Reply)
        [Start with empathy -> Brief professional insight (Cold-infusion logic) -> Soft product hint -> A gentle follow-up question]

        ### 3. 中文對照與意圖 (Translation & Intent)
        [中文翻譯，並說明為什麼這樣回覆能引導轉化]
        """

        # 获取最近几轮对话上下文
        context_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
        final_prompt = f"{system_instruction}\n\nRecent History:\n{context_history}\n\nLatest Query: {prompt_input}"

        # 9. 调用 AI 生成回复
        if model:
            with st.chat_message("assistant"):
                with st.spinner("正在思考最地道的表达..."):
                    try:
                        response = model.generate_content(final_prompt)
                        full_response = response.text
                        st.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    except Exception as e:
                        st.error(f"生成失败: {e}")
