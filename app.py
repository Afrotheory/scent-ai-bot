import streamlit as st
import google.generativeai as genai
import os
import pandas as pd

# 1. 页面配置
st.set_page_config(page_title="Eastern Scent Mentor", layout="wide")
st.title("🏯 東方香禮：專家導師與銷售系統")

# 2. 安全加載數據 (修復：確保 docs 缺失時不會崩潰)
@st.cache_data
def load_all_data():
    paths = {
        "tcm": "docs/TCM_Knowledge.md",
        "sop": "docs/SOP_Flow.md",
        "prices": "docs/Price_List_Optimized.csv",
        "sizes": "docs/Product_Sizes.md",
        "revival": "docs/Revival_Scripts.md"
    }
    lib = {}
    for k, v in paths.items():
        if os.path.exists(v):
            if v.endswith('.csv'): lib[k] = pd.read_csv(v)
            else: 
                with open(v, "r", encoding="utf-8") as f: lib[k] = f.read()
        else:
            lib[k] = "" if not v.endswith('.csv') else pd.DataFrame()
    return lib

lib = load_all_data()

# 3. Gemini 配置 (修復：API Key 缺失保護)
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ 系統配置錯誤：請在 Streamlit Secrets 中配置 GEMINI_API_KEY")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 導師控制中心")
    mode = st.radio("選擇任務模式:", 
                    ["🔍 專業診斷 (Mentor Mode)", 
                     "👅 舌診轉譯 (Tongue Analysis)", 
                     "✍️ 簡約回覆 (Casual Chat)",
                     "📊 產品導航表 (Catalog)"])
    st.divider()
    if st.button("🧹 清空對話歷史"):
        st.session_state.messages = []
        st.rerun()

# --- 核心邏輯處理 ---

# 模式 1：專業診斷 (修復：補全缺失邏輯)
if mode == "🔍 專業診斷 (Mentor Mode)":
    st.subheader("🔍 導師診斷與 SOP 策略")
    user_input = st.text_area("👉 粘貼客戶諮詢原話:", height=150)
    
    if st.button("生成專家方案", type="primary"):
        if user_input:
            prompt = f"""
            You are a Master Scent Mentor. 
            TASK: Analyze the user inquiry based on SOP and TCM Logic.
            
            STRUCTURE:
            1. MENTOR'S VOICE: Use induction and metaphors. Every English sentence must have Chinese translation.
            2. INTERNAL STRATEGY: Identify SOP stage from {lib.get('sop', '')}.
            3. REVIVAL HOOK: Suggest a hook from {lib.get('revival', '')} if customer stops replying.
            
            KNOWLEDGE: {lib.get('tcm', '')}
            INPUT: {user_input}
            """
            try:
                with st.spinner("導師正在分析..."):
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"AI 生成出錯，請稍後再試: {e}")

# 模式 2：舌診轉譯 (修復：增加異常保護與勾子引用)
elif mode == "👅 舌診轉譯 (Tongue Analysis)":
    st.subheader("👅 舌診專家轉譯 (不露聲色的誘導)")
    raw_report = st.text_area("👉 粘貼舌診 APP 的結論:", height=150)
    
    if st.button("生成誘導式建議", type="primary"):
        if raw_report:
            prompt = f"""
            You are a TCM Mentor. Translate this tongue report into an inductive consultation.
            REPORT: {raw_report}
            
            RULES:
            - Start with symptoms (Do you feel...?). 
            - Use analogies from {lib.get('tcm', '')}.
            - At the end, provide a 'Revival Script' from {lib.get('revival', '')} based on the recommended product.
            - English + Chinese for every sentence in Mentor Voice.
            """
            try:
                with st.spinner("轉譯中..."):
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"轉譯失敗: {e}")

# 模式 3：簡約回覆 (修復：增加異常保護)
elif mode == "✍️ 簡約回覆 (Casual Chat)":
    st.subheader("✍️ 簡約真人感回覆 (去 AI 化)")
    user_idea = st.text_area("👉 輸入中文點子:")
    
    if st.button("生成簡約英文"):
        if user_idea:
            prompt = f"""
            Act as a warm human mentor. Convert this into short, elegant English with Chinese translation: {user_idea}
            Style: Zen, warm, professional.
            """
            try:
                response = model.generate_content(prompt)
                st.success(response.text)
            except Exception as e:
                st.error(f"生成失敗: {e}")

# 模式 4：導航表
elif mode == "📊 產品導航表 (Catalog)":
    st.header("📊 全品類對照與價格清單")
    if isinstance(lib.get('prices'), pd.DataFrame) and not lib['prices'].empty:
        st.dataframe(lib['prices'], use_container_width=True, hide_index=True)
    else:
        st.warning("未找到價格數據，請檢查 Price_List_Optimized.csv")
    st.markdown(lib.get('sizes', "未找到尺寸表"))
