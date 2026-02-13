import streamlit as st
import google.generativeai as genai
import os

# 1. 頁面配置
st.set_page_config(page_title="Scent Curator Assistant", layout="wide")
st.title("🏯 東方香禮跨境行銷專業助手")
st.markdown("---")

# 2. 初始化對話記憶
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. 讀取知識庫
@st.cache_data
def load_docs():
    try:
        docs = {}
        files = {
            "sop": "docs/SOP_Flow.md",
            "product": "docs/Product_Info.md",
            "sizes": "docs/Product_Sizes.md",
            "prices": "docs/Price_List.md"
        }
        for key, path in files.items():
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    docs[key] = f.read()
            else:
                docs[key] = f"未找到文件: {path}"
        return docs
    except Exception as e:
        st.error(f"讀取文檔出錯: {e}")
        return None

docs_content = load_docs()

# 4. 配置 Gemini
gemini_key = st.secrets.get("GEMINI_API_KEY")
if not gemini_key:
    st.error("請在 Secrets 中配置 GEMINI_API_KEY")
elif not docs_content:
    st.warning("請檢查 docs 資料夾內是否有 SOP_Flow.md、Product_Info.md、Product_Sizes.md、Price_List.md。")
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

    # --- 側邊欄：模式選擇 ---
    with st.sidebar:
        st.header("⚙️ 操作中心")
        mode = st.radio("功能切換:", ["分析客戶詢盤 (Diagnosis)", "輔助我寫回覆 (Creative Mode)"])
        if st.button("清除對話記錄"):
            st.session_state.messages = []
            st.rerun()
        st.divider()
        st.caption("版本: v2.5 (視覺強化版)")

    # 5. 輸入區
    if mode == "分析客戶詢盤 (Diagnosis)":
        user_input = st.text_area("👉 粘貼客戶的原話:", height=150, placeholder="例如: I've been feeling very stressed lately...")
        instruction = "分析客戶目前的SOP階段、潛在痛點，並給出專業建議和1-3句的英文回覆。最後必須提供中文翻譯。"
    else:
        user_input = st.text_area("👉 輸入你想表達的中文點子:", height=150, placeholder="例如: 告訴他麒麟竭適合運動後消腫，建議他買14mm的。")
        instruction = "將我的中文點子轉化為地道、優雅的療癒師口吻英文。必須包含產品特點，控制在3句內，並提供中文翻譯。"

    if st.button("生成專家方案", type="primary"):
        if not user_input:
            st.warning("請輸入內容")
        else:
            # 構建 Prompt
            system_prompt = f"""
            You are a "Scent Healing Mentor" (Eastern Scent Therapist).
            Library:
            - Products: {docs_content['product']}
            - SOP: {docs_content['sop']}
            - Prices: {docs_content['prices']}
            - Sizes: {docs_content['sizes']}

            Rules:
            1. Tone: Elegant, Professional, Empathetic.
            2. Concise: English reply MUST be 1-3 sentences.
            3. Mandatory Structure:
               ### 1. 內部診斷與策略
               - 包含SOP階段、痛點分析、追問建議、以及[追問短句的中文翻譯]。
               ### 2. 建議英文回覆
               ### 3. 中文參考 (Translation)
            """

            with st.spinner("正在調度產品資料庫與視覺素材..."):
                try:
                    history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-3:]])
                    response = model.generate_content(f"{system_prompt}\n\nTask: {instruction}\nInput: {user_input}\nContext: {history}")

                    # 顯示文字結果
                    st.markdown("---")
                    st.subheader("💡 專家回覆建議")
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    st.session_state.messages.append({"role": "assistant", "content": response.text})

                    # 6. 視覺化圖片匹配模塊
                    st.divider()
                    st.subheader("🖼️ 推薦發送的視覺資料")

                    # --- 35款產品全量映射表 (完整版) ---
                    product_map = {
                        # 核心爆款
                        "麒麟竭": "qi_lin_blood_resin", "Dragon's Blood": "qi_lin_blood_resin", "龙瑞": "qi_lin_blood_resin",
                        "泣血蜀魄": "soul_of_shupo", "Soul of Shupo": "soul_of_shupo", "烈火蜀魄": "soul_of_shupo",
                        "大苏合": "grand_suhe_incense", "Grand Suhe": "grand_suhe_incense",
                        "红麝": "red_musk", "Red Musk": "red_musk",

                        # 高階/中階系列
                        "五方贵人": "the_five_elemental_guardians", "Five Elemental": "the_five_elemental_guardians",
                        "安宫牛黄": "an_gong_niu_huang", "An Gong": "an_gong_niu_huang",
                        "鹅梨": "midnight_pear_in_the_canopy", "Midnight Pear": "midnight_pear_in_the_canopy",
                        "内府龙涎": "imperial_dragon_s_breath", "Dragon's Breath": "imperial_dragon_s_breath",
                        "御制白龙涎": "white_dragon_s_realm", "White Dragon": "white_dragon_s_realm",
                        "御制黑龙涎": "imperial_dragon_s_nectar", "Black Dragon": "imperial_dragon_s_nectar",
                        "紫油降真": "purple_oil_jiangzhen_incense", "Jiangzhen": "purple_oil_jiangzhen_incense",
                        "芳华茉莉": "youthful_jasmine", "Youthful Jasmine": "youthful_jasmine",
                        "花蕊夫人": "madame_huarui", "Madame Huarui": "madame_huarui",
                        "返魂香": "fantian_xiang", "Return-Soul": "fantian_xiang",
                        "归元香": "returning_to_the_origin", "Returning to Origin": "returning_to_the_origin",
                        "孔韵迷迭": "confucian_charm_rosemary", "Confucian Charm": "confucian_charm_rosemary",
                        "紫气东来": "the_eastern_purple_qi_arrives", "Purple Qi": "the_eastern_purple_qi_arrives",
                        "傅延年": "fu_yan_nian", "Fu Yan Nian": "fu_yan_nian",
                        "汉宫椒房": "the_jiaofang", "Jiaofang": "the_jiaofang",
                        "龙涎紫雪": "long_yan_zi_xue", "Long Yan Zi Xue": "long_yan_zi_xue",

                        # 香牌/其他
                        "龙瑞凤九": "dragon_phoenix_card",
                        "马上有钱": "horse_wealth",
                        "湖蓝龙梅": "blue_imperial_plum_card",
                        "紫薇讳": "ziwei_talisman",
                        "苏合香牌": "suhe_card",
                        "人参莲花": "ginseng_lotus",
                        "福梳": "blessing_comb",
                        "茉莉身体乳": "jasmine_lotion",
                        "松塔": "pine_cone",
                        "驱疫香": "epidemic_protection",
                        "安眠安神": "sleep_aid",
                        "沉香": "agarwood", "檀香": "sandalwood"
                    }

                    matched = False
                    for key, slug in product_map.items():
                        if key.lower() in user_input.lower() or key.lower() in response.text.lower():
                            matched = True
                            st.write(f"**匹配產品: {key}**")
                            c1, c2 = st.columns(2)
                            with c1:
                                st.image(f"images/{slug}_style.jpg", caption="款式展示图")
                            with c2:
                                st.image(f"images/{slug}_ing.jpg", caption="成分功效图")

                    if not matched:
                        st.info("當前對話未匹配到特定產品圖片，若需查看請輸入具體產品名稱。")

                except Exception as e:
                    st.error(f"方案生成失敗: {e}")

    # 顯示對話歷史
    with st.expander("📜 查看對話歷史"):
        for m in st.session_state.messages:
            st.write(f"{m['role']}: {m['content']}")
