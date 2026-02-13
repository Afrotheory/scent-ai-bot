import streamlit as st
import google.generativeai as genai
import os

# 1. 頁面配置
st.set_page_config(page_title="Scent Curator Assistant", layout="wide")
st.title("🏯 東方香禮：中醫合香百科專家系統")
st.markdown("---")

# 2. 初始化對話記憶
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. 讀取知識庫 (核心：優先加載 TCM 百科)
@st.cache_data
def load_all_libraries():
    try:
        paths = {
            "tcm": "docs/TCM_Knowledge.md",
            "sop": "docs/SOP_Flow.md",
            "product": "docs/Product_Info.md",
            "sizes": "docs/Product_Sizes.md",
            "prices": "docs/Price_List.md"
        }
        lib = {}
        for key, path in paths.items():
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    lib[key] = f.read()
            else:
                lib[key] = "" # 容錯處理
        return lib
    except Exception as e:
        st.error(f"讀取資料庫失敗: {e}")
        return None

lib = load_all_libraries()

# 4. 配置 Gemini 引擎
gemini_key = st.secrets.get("GEMINI_API_KEY")
if not gemini_key or not lib:
    st.error("系統配置未完成，請檢查 API Key 或 docs 文件。")
else:
    genai.configure(api_key=gemini_key)
    
    @st.cache_resource
    def get_brain():
        try:
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target = next((m for m in models if 'gemini-1.5-flash' in m), models[0])
            return genai.GenerativeModel(model_name=target)
        except:
            return genai.GenerativeModel('gemini-1.5-flash')

    model = get_brain()

    # --- 側邊欄：控制中心 ---
    with st.sidebar:
        st.header("⚙️ 模式切換")
        mode = st.radio("當前任務 (Select Task):", 
                        ["🔍 診斷模式 (Diagnosis)", "✍️ 創作模式 (Creative/Translation)", "📊 產品導航 (Catalog & Pricing)"])
        st.divider()
        if st.button("🧹 清理對話歷史"):
            st.session_state.messages = []
            st.rerun()
        st.caption("AI 核心已連結：TCM_Knowledge.md")

    # 5. 輸入界面佈局
    if mode == "🔍 診斷模式 (Diagnosis)":
        user_input = st.text_area("👉 粘貼客戶諮詢原話:", height=180, placeholder="客戶說膝蓋冷痛...")
        mode_instruction = f"""
        TASK: DIAGNOSTIC_ANALYSIS
        1. CROSS-REFERENCE: Use the TCM Library ({lib['tcm']}) to find the specific syndrome.
        2. SOP: Identify the stage from {lib['sop']}.
        3. OUTPUT: Strategy -> English Response -> Translation.
        """
    else:
        user_input = st.text_area("👉 輸入你想表達的中醫點子 / 銷售要點:", height=180, placeholder="告訴他黑龍涎能消積利水，契合結石調理思路...")
        mode_instruction = f"""
        TASK: CREATIVE_TRANSLATION
        1. NO SOP: Skip SOP analysis entirely.
        2. TCM ENHANCEMENT: Extract professional logic (e.g., 'Fluid Metabolism', 'Stagnation Clearing') from {lib['tcm']} based on the user's input.
        3. POLISH: Translate the ideas into high-end, elegant English.
        """
    else:
        st.header("📊 全品類中英對照及報價清單")
        st.info("💡 提示：你可以使用下表右上角的放大鏡或搜尋功能快速查找產品名稱或尺寸。")

        try:
            import pandas as pd

            catalog_data = [
                {"產品": "麒麟竭/龍瑞", "English Name": "Dragon's Blood / Long Rui", "規格": "10mm/14mm/18mm", "供貨價(￥)": "1343起", "最低控價(￥)": "3298起", "起步定價($)": "499起"},
                {"產品": "泣血蜀魄", "English Name": "Soul of Shupo", "規格": "10mm/14mm/18mm", "供貨價(￥)": "532起", "最低控價(￥)": "1669起", "起步定價($)": "267起"},
                {"產品": "黑龍涎", "English Name": "Imperial Black Dragon Nectar", "規格": "10mm/14mm/18mm", "供貨價(￥)": "1343起", "最低控價(￥)": "3298起", "起步定價($)": "499起"},
                {"產品": "紅麝/四合香", "English Name": "Red Musk / Four-in-One", "規格": "10mm/14mm/18mm", "供貨價(￥)": "2567起", "最低控價(￥)": "4068起", "起步定價($)": "609起"},
                {"產品": "安宮牛黃", "English Name": "An Gong Niu Huang", "規格": "10mm/14mm/18mm", "供貨價(￥)": "1343起", "最低控價(￥)": "3600起", "起步定價($)": "542起"},
                {"產品": "傅延年", "English Name": "Fu Yan Nian (Vitality)", "規格": "10mm/14mm/18mm", "供貨價(￥)": "2567起", "最低控價(￥)": "4068起", "起步定價($)": "609起"},
                {"產品": "漢宮椒房", "English Name": "The Jiaofang (Warming)", "規格": "10mm/14mm/18mm", "供貨價(￥)": "1343起", "最低控價(￥)": "3298起", "起步定價($)": "499起"},
                {"產品": "馬上有錢", "English Name": "Success & Wealth (Horse)", "規格": "香牌 30*36mm", "供貨價(￥)": "36", "最低控價(￥)": "129", "起步定價($)": "-"},
                {"產品": "人參蓮花", "English Name": "Ginseng Lotus", "規格": "香牌 43*43mm", "供貨價(￥)": "42", "最低控價(￥)": "168", "起步定價($)": "-"},
            ]
            df = pd.DataFrame(catalog_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("📏 尺寸參考 (Size Reference)")
            size_data = lib.get("sizes", "")
            st.markdown(size_data if size_data else "未找到尺寸資料。")
        except Exception as e:
            st.error(f"表格解析失敗，請手動檢查 Price_List.md 格式。 錯誤: {e}")

        user_input = ""
        mode_instruction = ""

    if mode != "📊 產品導航 (Catalog & Pricing)" and st.button("🚀 生成專家方案", type="primary"):
        if not user_input:
            st.warning("請輸入內容。")
        else:
            # 核心指令：強制知識庫優先
            system_instruction = f"""
            You are a "Master Scent Therapist."
            MANDATORY: You must prioritize the facts in the provided TCM Library over general AI knowledge.

            【Core Libraries】
            - TCM Knowledge: {lib['tcm']}
            - Product Specs: {lib['product']} | {lib['sizes']} | {lib['prices']}

            【Formatting Guide】
            Regardless of mode, always structure as:
            ### 1. 療癒師內部邏輯 (Logic & Strategy)
            - [Modes specifics: TCM diagnosis or Creative intent]
            - [Suggested chase-up strategy + Chinese translation]
            
            ### 2. 建議英文回覆 (Mentor's Reply)
            [1-3 sentences of Zen-like, professional English.]

            ### 3. 中文參考 (Translation)
            [Accurate Chinese translation of Section 2.]
            """

            with st.spinner("AI 正在深度檢索中醫知識庫..."):
                try:
                    history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-3:]])
                    full_query = f"{system_instruction}\n\n{mode_instruction}\nInput: {user_input}\nContext: {history}"
                    
                    response = model.generate_content(full_query)
                    answer = response.text
                    
                    # 顯示文字結果
                    st.markdown("---")
                    st.subheader("💡 生成結果")
                    st.markdown(answer)
                    
                    # 7. 視覺化組件：圖片自動匹配
                    st.divider()
                    st.subheader("🖼️ 推薦視覺素材")
                    
                    # 擴展至 35 款產品的 Slug 對應 (部分示例，可按 CSV 繼續補充)
                    product_map = {
                        "麒麟竭": "qi_lin_blood_resin", "龍瑞": "qi_lin_blood_resin",
                        "蜀魄": "soul_of_shupo", "泣血": "soul_of_shupo",
                        "黑龍涎": "grand_suhe_incense", "白龍涎": "white_dragon_s_realm",
                        "紅麝": "red_musk", "四合香": "red_musk",
                        "傅延年": "fu_yan_nian", "漢宮椒房": "the_jiaofang"
                    }

                    matched = False
                    for key, slug in product_map.items():
                        if key.lower() in user_input.lower() or key.lower() in answer.lower():
                            matched = True
                            st.write(f"✅ **匹配資料: {key}**")
                            c1, c2 = st.columns(2)
                            with c1: st.image(f"images/{slug}_style.jpg", caption="款式展示")
                            with c2: st.image(f"images/{slug}_ing.jpg", caption="中醫配方/功效")
                    
                    if not matched: st.info("未檢索到特定產品圖片。")

                    st.session_state.messages.append({"role": "user", "content": user_input})
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    st.error(f"生成失敗: {e}")
