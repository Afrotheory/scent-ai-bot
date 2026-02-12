import streamlit as st
import google.generativeai as genai

# 1. 頁面配置
st.set_page_config(page_title="Scent Curator Assistant", layout="centered")
st.title("🏯 東方香禮跨境營銷助手 (專業版)")

# 2. 初始化對話記憶
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. 讀取知識庫 (緩存處理)
@st.cache_data
def load_docs():
    try:
        with open("docs/SOP_Flow.md", "r", encoding="utf-8") as f:
            sop = f.read()
        with open("docs/Product_Info.md", "r", encoding="utf-8") as f:
            product = f.read()
        with open("docs/Product_Sizes.md", "r", encoding="utf-8") as f:
            sizes = f.read()
        with open("docs/Price_List.md", "r", encoding="utf-8") as f:
            prices = f.read()
        return sop, product, sizes, prices
    except Exception as e:
        st.error(f"讀取文件失敗: {e}")
<<<<<<< HEAD
        return "", ""
=======
        return "", "", "", ""
>>>>>>> b33d084 (feat: add Product_Sizes & Price_List, pricing/sizing logic in prompt)

sop_content, product_content, size_content, price_content = load_docs()

# 4. 配置 Gemini (包含 404 兼容性修復)
gemini_key = st.secrets.get("GEMINI_API_KEY")
if not gemini_key:
    st.error("請在 Secrets 中配置 GEMINI_API_KEY")
else:
    genai.configure(api_key=gemini_key)
    
    # 動態獲取模型名稱，防止硬編碼 404
    @st.cache_resource
    def get_model():
        try:
            # 優先尋找 1.5-flash，若無則選第一個支持生成內容的模型
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target = next((m for m in models if 'gemini-1.5-flash' in m), models[0])
            return genai.GenerativeModel(model_name=target)
        except Exception:
            # 保底方案
            return genai.GenerativeModel('gemini-1.5-flash')

    model = get_model()

    with st.sidebar:
        if st.button("清除對話記錄 (Clear Chat)"):
            st.session_state.messages = []
            st.rerun()

    # 5. 顯示歷史對話
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 6. 用戶輸入與處理
    if prompt := st.chat_input("在此粘貼客戶的話..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 核心指令：強化療愈師人設 + 1-3句限制 + 帶翻譯的追問
        system_instruction = f"""
<<<<<<< HEAD
        You are an "Eastern Scent Therapist." Build trust via concise, professional diagnosis.
=======
        You are an "Eastern Scent Therapist." Your goal: Build trust via concise, professional diagnosis.
>>>>>>> b33d084 (feat: add Product_Sizes & Price_List, pricing/sizing logic in prompt)

        【Core Knowledge】
        SOP: {sop_content}
        Products: {product_content}
        Sizes & Lengths: {size_content}
        Prices (USD): {price_content}

<<<<<<< HEAD
        【Communication Rules - MANDATORY】
        1. STRIKE THE CHAT-KILLER: English replies MUST be 1-3 short, natural sentences.
        2. DIAGNOSIS (望聞問切): If symptoms are mentioned, ask ONLY ONE specific follow-up question.
        3. CHASE-UP STRATEGY: Provide a ultra-short (max 2 sentences) follow-up text with its Chinese translation.
        4. TRANSLATION: Every English text provided must have a corresponding Chinese translation.
=======
        【Pricing & Sizing Logic】
        1. NO PRICE DUMPING: Don't give prices in the "Discovery" stage.
        2. QUOTE SMARTLY: If the customer asks for price, explain the value first (hand-steps, aging), then provide the USD price for the 10mm (Standard Women's) or 14mm (Standard Men's) specific to their wrist size.
        3. SIZE GUIDE: Use inches (e.g., 6.0" - 6.5") when describing sizes to help Western customers understand the fit.

        【Communication Rules】
        1. THE SKEPTIC'S GUIDE: If a customer is skeptical, explain the "Transdermal Absorption" and "Olfactory Neural Response" in a sophisticated way (Botanical energy interacting with body heat).
        2. VASCULAR & NERVOUS FOCUS (望聞問切): When symptoms are mentioned, DO NOT jump to products. First, generate 1-2 caring follow-up questions to understand their lifestyle (e.g., stress levels, sleep patterns, or pain triggers).
        3. ANTI-CHAT-END: Every reply must end with a gentle question or an emotional hook to keep the conversation alive.
        4. ROLE: You are an expert friend. Use "I've seen similar cases...", "In our tradition, we believe...", "Actually, your body is telling you...".
>>>>>>> b33d084 (feat: add Product_Sizes & Price_List, pricing/sizing logic in prompt)

        【Output Structure】
        ### 1. 療癒師內部策略 (Internal Analysis)
        - **SOP 階段**: [目前階段]
        - **望聞問切 (Diagnosis)**: [分析症狀，並給出一個精準的專業詢問點]
        - **追問策略 (Chase-up)**: [若客戶沒回，可用短句]
        - **追問中文翻譯**: [翻譯上面的追問短句]
        - **策略意圖**: [為什麼這樣能轉化]

        ### 2. 建議英文回覆 (The Mentor's Reply)
        [1-3 sentences of elegant English. Must end with a gentle question.]

        ### 3. 中文參考 (Translation)
        [上述英文回覆的對應中文]
        """

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
                    full_query = f"{system_instruction}\n\nRecent History:\n{history}\n\nLatest Query: {prompt}"
                    
                    response = model.generate_content(full_query)
                    answer = response.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"發生錯誤: {e}")
