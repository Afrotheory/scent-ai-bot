import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import json
from datetime import datetime, timedelta

# 1. 页面配置
st.set_page_config(page_title="Eastern Scent Mentor", layout="wide")
st.title("🏯 東方香禮：專家導師與銷售系統")

if "messages" not in st.session_state:
    st.session_state.messages = []

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

@st.cache_resource
def get_model():
    try:
        models = [
            m.name
            for m in genai.list_models()
            if "generateContent" in getattr(m, "supported_generation_methods", [])
        ]
        preferred = ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]

        # 先按偏好匹配
        for pref in preferred:
            for m in models:
                if pref in m:
                    return genai.GenerativeModel(model_name=m), m

        # 再用第一個可用模型兜底
        if models:
            return genai.GenerativeModel(model_name=models[0]), models[0]
    except Exception:
        pass

    # 最後兜底（部分環境只认短名）
    return genai.GenerativeModel("gemini-1.5-flash"), "gemini-1.5-flash"


model, active_model = get_model()

CUSTOMER_DIR = "docs/customers"


def ensure_customer_dir():
    os.makedirs(CUSTOMER_DIR, exist_ok=True)


def _safe_client_name(name: str) -> str:
    return "".join(ch for ch in name.strip() if ch not in r'\/:*?"<>|').strip()


def _client_path(client_name: str) -> str:
    return os.path.join(CUSTOMER_DIR, f"{client_name}.json")


def create_client_profile(raw_name: str):
    ensure_customer_dir()
    name = _safe_client_name(raw_name)
    if not name:
        st.sidebar.warning("請先輸入有效客戶名稱。")
        return
    path = _client_path(name)
    if os.path.exists(path):
        st.sidebar.info(f"客戶「{name}」已存在。")
        return
    payload = {
        "client": name,
        "created_at": datetime.utcnow().isoformat(),
        "last_customer_reply_at": None,
        "history": [],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    st.sidebar.success(f"已建立客戶檔案：{name}")


def get_all_clients():
    ensure_customer_dir()
    clients = []
    for fn in os.listdir(CUSTOMER_DIR):
        if fn.lower().endswith(".json"):
            clients.append(fn[:-5])
    clients.sort()
    return clients if clients else ["(尚無客戶，請先建立)"]


def _load_client_doc(client_name: str):
    if client_name.startswith("("):
        return None
    path = _client_path(client_name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_client_doc(client_name: str, doc: dict):
    path = _client_path(client_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)


def append_client_history(client_name: str, role: str, text: str):
    doc = _load_client_doc(client_name)
    if doc is None:
        return
    doc.setdefault("history", []).append(
        {"ts": datetime.utcnow().isoformat(), "role": role, "text": text}
    )
    if role == "customer":
        doc["last_customer_reply_at"] = datetime.utcnow().isoformat()
    _save_client_doc(client_name, doc)


def load_client_history(client_name: str):
    doc = _load_client_doc(client_name)
    if not doc:
        return ""
    lines = []
    for item in doc.get("history", []):
        lines.append(f"{item.get('role', 'unknown')}: {item.get('text', '')}")
    return "\n".join(lines[-30:])


def check_if_silent(client_name: str):
    doc = _load_client_doc(client_name)
    if not doc:
        return False
    ts = doc.get("last_customer_reply_at")
    if not ts:
        return False
    try:
        last = datetime.fromisoformat(ts)
    except ValueError:
        return False
    return datetime.utcnow() - last > timedelta(hours=24)


def generate_revival_hook(client_name: str):
    context = load_client_history(client_name)
    prompt = f"""
    You are a top closer for premium scent products.
    Write one short revival message to wake up a silent customer.
    Tone: warm, confident, non-pushy.
    Include: 1 emotional hook + 1 soft question.
    If possible, align with this script bank: {lib.get('revival', '')}
    Context: {context}
    Output only the message text.
    """
    try:
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except Exception:
        return "Hi, I just thought of you because your last concern was important — would you like me to give you a simpler option that feels easier to start with?"


def apply_sales_touch(text: str, user_intent: str):
    # 如果检测到客户在谈论病痛或困扰
    if any(word in user_intent.lower() for word in ["brain fog", "insomnia", "surgery", "tired"]):
        return f"Oh, I totally feel you, sister! Actually... {text}"
    return text


def manage_customers():
    st.sidebar.header("👥 客戶管理中心")
    new_client = st.sidebar.text_input("➕ 新建客戶 (輸入姓名/編號):")
    if st.sidebar.button("創建"):
        create_client_profile(new_client)
    return st.sidebar.selectbox("🎯 當前服務對象:", get_all_clients())

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 導師控制中心")
    mode = st.radio("選擇任務模式:", 
                    ["🔍 專業診斷 (Mentor Mode)", 
                     "👅 舌診轉譯 (Tongue Analysis)", 
                     "✍️ 簡約回覆 (Casual Chat)",
                     "📊 產品導航表 (Catalog)",
                     "🏆 金牌實戰對話"])
    st.caption(f"當前模型：{active_model}")
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

            SALES TACTIC: 
            1. Use warm greetings like "Dear sister" or "Honey" depending on the vibe.
            2. If they mention a symptom (like Brain Fog), react with excitement: "Yes! You found the right place."
            3. Compliment them! If they show a photo, say their wrist or energy is beautiful.
            4. Don't just answer—connect.
            
            KNOWLEDGE: {lib.get('tcm', '')}
            INPUT: {user_input}
            """
            try:
                with st.spinner("導師正在分析..."):
                    response = model.generate_content(prompt)
                    final_text = apply_sales_touch(response.text, user_input)
                    st.markdown(final_text)
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

            SALES TACTIC:
            1. Use warm greetings like "Dear sister" or "Honey" depending on the vibe.
            2. If they mention a symptom (like Brain Fog), react with excitement: "Yes! You found the right place."
            3. Compliment them! If they show a photo, say their wrist or energy is beautiful.
            4. Don't just answer—connect.
            """
            try:
                with st.spinner("轉譯中..."):
                    response = model.generate_content(prompt)
                    final_text = apply_sales_touch(response.text, raw_report)
                    st.markdown(final_text)
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

            SALES TACTIC:
            1. Use warm greetings like "Dear sister" or "Honey" depending on the vibe.
            2. If they mention a symptom (like Brain Fog), react with excitement: "Yes! You found the right place."
            3. Compliment them! If they show a photo, say their wrist or energy is beautiful.
            4. Don't just answer—connect.
            """
            try:
                response = model.generate_content(prompt)
                final_text = apply_sales_touch(response.text, user_idea)
                st.success(final_text)
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

# 模式 5：金牌實戰對話
elif mode == "🏆 金牌實戰對話":
    client = manage_customers()
    st.subheader(f"正在與 {client} 對話中...")

    latest_msg = st.text_area("👉 粘貼客戶最新回覆:", height=100)

    if st.button("獲取金牌回覆建議"):
        if client.startswith("("):
            st.warning("請先建立客戶檔案。")
        elif not latest_msg.strip():
            st.warning("請先粘貼客戶最新回覆。")
        else:
            append_client_history(client, "customer", latest_msg.strip())
            context = load_client_history(client)
            prompt = f"""
            CONTEXT: {context}
            NEW MESSAGE: {latest_msg}
            TASK: 模仿金牌銷售，分析客戶情緒，給出下一步開單建議。
            請輸出：
            1) 當前客戶情緒與階段判斷
            2) 下一步建議話術（英文）
            3) 中文翻譯

            SALES TACTIC:
            1. Use warm greetings like "Dear sister" or "Honey" depending on the vibe.
            2. If they mention a symptom (like Brain Fog), react with excitement: "Yes! You found the right place."
            3. Compliment them! If they show a photo, say their wrist or energy is beautiful.
            4. Don't just answer—connect.
            """
            try:
                response = model.generate_content(prompt)
                final_text = apply_sales_touch(response.text, latest_msg)
                st.write(final_text)
                append_client_history(client, "assistant", final_text)
            except Exception as e:
                st.error(f"生成失敗: {e}")

    if check_if_silent(client):
        st.warning("🏮 該客戶已超過24小時未回覆")
        if st.button("生成喚醒勾子"):
            hook = generate_revival_hook(client)
            st.code(hook)
