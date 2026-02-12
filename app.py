import streamlit as st
import google.generativeai as genai

# 1. 頁面配置
st.set_page_config(page_title="Scent Curator Assistant", layout="wide")
st.title("🏯 東方香禮跨境行銷專業助手")
st.markdown("---")

# 2. 初始化對話記憶
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. 讀取知識庫 (緩存處理)
@st.cache_data
def load_docs():
    try:
        paths = {
            "sop": "docs/SOP_Flow.md",
            "product": "docs/Product_Info.md",
            "sizes": "docs/Product_Sizes.md",
            "prices": "docs/Price_List.md"
        }
        content = {}
        for key, path in paths.items():
            with open(path, "r", encoding="utf-8") as f:
                content[key] = f.read()
        return content
    except Exception as e:
        st.error(f"讀取文件失敗，請確保 docs 資料夾內有對應的 MD 文件: {e}")
        return None

docs = load_docs()

# 4. 配置 Gemini
gemini_key = st.secrets.get("GEMINI_API_KEY")
if not gemini_key or not docs:
    st.warning("請檢查 Secrets 配置或 docs 文件是否完整。")
else:
    genai.configure(api_key=gemini_key)

    @st.cache_resource
    def get_model():
        try:
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target = next((m for m in models if 'gemini-1.5-flash' in m), models[0])
            return genai.GenerativeModel(model_name=target)
        except Exception:
            return genai.GenerativeModel('gemini-1.5-flash')

    model = get_model()

    # --- 側邊欄：功能與清理 ---
    with st.sidebar:
        st.header("⚙️ 設定")
        mode = st.radio("選擇操作模式 (Mode):",
                        ["分析客戶詢盤 (Diagnosis)", "創作/翻譯回覆 (Creative Translation)"])
        if st.button("清除對話記錄 (Clear Chat)"):
            st.session_state.messages = []
            st.rerun()
        st.info("💡 「分析模式」用於判斷客戶意圖；「創作模式」幫你把中文點子變為地道英文。")

    # 5. 主界面佈局
    if mode == "分析客戶詢盤 (Diagnosis)":
        user_input = st.text_area("👉 粘貼客戶的原話 (Paste Customer Query):", height=150, placeholder="例如: I have trouble sleeping, what do you recommend?")
        instruction_type = "DIAGNOSTIC_ANALYSIS"
    else:
        user_input = st.text_area("👉 輸入你想表達的中文要點 (What do you want to say?):", height=150, placeholder="例如: 告訴他麒麟竭適合運動損傷，我們需要45天窖藏，所以現在只有少量現貨。")
        instruction_type = "CREATIVE_RESPONSE"

    if st.button("生成專家方案 (Generate)"):
        if not user_input:
            st.warning("請先輸入內容再生成。")
        else:
            # 6. 核心系統指令構建
            system_instruction = f"""
            You are a "Scent Healing Mentor." Build trust via professionalism and elegance.

            【Library】
            - SOP: {docs['sop']}
            - Products: {docs['product']}
            - Sizes: {docs['sizes']}
            - Prices: {docs['prices']}

            【Rules】
            1. TONE: Elegant, empathetic, and Zen-like.
            2. CONCISE: English output must be 1-3 sentences. No long paragraphs.
            3. PRICING: If asked about price, quote USD strictly from the list.
            4. MODE - {instruction_type}:
               - If DIAGNOSTIC: Analyze the customer's SOP stage and pain points. Ask ONE professional follow-up question.
               - If CREATIVE: Translate the user's Chinese points into elegant English, integrating specific product terms like "Cellar-aged" or "13 sacred hand-steps" from the library.
            """

            with st.spinner("AI 正在結合產品知識庫思考中..."):
                try:
                    # 獲取最近對話背景
                    history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-3:]])

                    if instruction_type == "DIAGNOSTIC_ANALYSIS":
                        query = f"{system_instruction}\n\n[Analyze this customer]: {user_input}\n\n[History]: {history}"
                    else:
                        query = f"{system_instruction}\n\n[Translate and polish this Chinese idea into mentor-style English]: {user_input}\n\n[History]: {history}"

                    response = model.generate_content(query)

                    # 7. 顯示結果
                    st.markdown("---")
                    st.subheader("💡 專家建議方案")
                    st.markdown(response.text)

                    # 記錄對話
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"發生錯誤: {e}")

    # 顯示歷史紀錄 (折疊顯示)
    with st.expander("📜 查看最近對話歷史"):
        for m in st.session_state.messages:
            st.write(f"**{m['role']}**: {m['content']}")
