import streamlit as st
import google.generativeai as genai

# 1. 頁面配置
st.set_page_config(page_title="Scent Curator Assistant", layout="centered")
st.title("🏯 東方香禮跨境營銷助手 (專業版)")

# 2. 初始化對話記憶
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. 讀取知識庫
@st.cache_data
def load_docs():
    try:
        with open("docs/SOP_Flow.md", "r", encoding="utf-8") as f:
            sop = f.read()
        with open("docs/Product_Info.md", "r", encoding="utf-8") as f:
            product = f.read()
        return sop, product
    except Exception as e:
        st.error(f"讀取文件失敗: {e}")
        return "", ""

sop_content, product_content = load_docs()

# 4. 配置 Gemini
gemini_key = st.secrets.get("GEMINI_API_KEY")
if not gemini_key:
    st.error("請在 Secrets 中配置 GEMINI_API_KEY")
else:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    with st.sidebar:
        if st.button("清除對話記錄 (Clear Chat)"):
            st.session_state.messages = []
            st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("在此粘貼客戶的話..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # --- 核心指令重構 (注意這裡的縮進) ---
        system_instruction = f"""
        You are an "Eastern Scent Therapist." Your goal: Build trust via concise, professional diagnosis. 

        【Core Knowledge】
        SOP: {sop_content}
        Products: {product_content}

        【Communication Rules - MANDATORY】
        1. STRIKE THE CHAT-KILLER: No long paragraphs. English replies MUST be 1-3 short, natural sentences.
        2. DIAGNOSIS (望聞問切): If a symptom is mentioned, ask ONLY ONE specific follow-up question.
        3. CHASE-UP STRATEGY: Provide a ultra-short (max 2 sentences) follow-up text with its Chinese translation.
        4. TRANSLATION: Every English text provided must have a corresponding Chinese translation.

        【Output Structure - Follow Strictly】
        ### 1. 療癒師內部策略 (Internal Analysis)
        - **SOP 階段**: [目前階段]
        - **望聞問切 (Diagnosis)**: [分析症狀，並給出一個精準的「專業詢問點」]
        - **追問策略 (Chase-up)**: [若客戶沒回，隔天可用的「1-2句」短句]
        - **策略中文意圖**: [中文翻譯及為什麼這樣能觸達客戶]

        ### 2. 建議英文回覆 (The Mentor's Reply)
        [1-3 sentences of elegant English. Must end with a gentle question.]

        ### 3. 中文參考 (Translation)
        [上述英文回覆的對應中文]
        """

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
                    full_prompt = f"{system_instruction}\n\nHistory:\n{history_context}\n\nLatest Query: {prompt}"
                    
                    response = model.generate_content(full_prompt)
                    answer = response.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"生成失敗: {e}")
