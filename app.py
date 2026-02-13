import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import re

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
        3. MANDATORY OUTPUT: You MUST explicitly state SOP stage in Section 1, e.g. "Stage 3: Education & Storytelling".
        4. OUTPUT: Strategy -> English Response -> Translation.
        """
    elif mode == "✍️ 創作模式 (Creative/Translation)":
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
            if mode == "🔍 診斷模式 (Diagnosis)":
                mode_specific_rule = (
                    "In Section 1, SOP stage is REQUIRED and cannot be omitted. "
                    "Also include pain-point mapping to one concrete product family. "
                    "Section 1 must include a Chinese translation for the logic points."
                )
            else:
                mode_specific_rule = (
                    "In Creative mode, do not output SOP stage. Focus on polished translation and persuasive product storytelling. "
                    "Section 1 still needs a short Chinese translation of the creative intent."
                )

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
            - [Chinese Translation of Section 1: translate your logic/strategy into concise Chinese]
            - [Suggested chase-up strategy + Chinese translation]
            
            ### 2. 建議英文回覆 (Mentor's Reply)
            [1-3 sentences of Zen-like, professional English.]

            ### 3. 中文參考 (Translation)
            [Accurate Chinese translation of Section 2.]

            【Mode-specific Constraint】
            {mode_specific_rule}
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
                    
                    # --- 視覺化組件：從 CSV 動態匹配圖片 ---
                    st.divider()
                    st.subheader("🖼️ 推薦視覺素材")

                    @st.cache_data
                    def load_image_map():
                        csv_path = "docs/product_image_filenames.csv"
                        if os.path.exists(csv_path):
                            return pd.read_csv(csv_path)
                        return None

                    image_df = load_image_map()

                    if image_df is not None:
                        # 只根據 AI 回覆內容匹配，避免按客戶原話誤觸發多產品
                        answer_lower = answer.lower()
                        section2_match = re.search(
                            r"###\s*2\..*?(?=###\s*3\.|$)",
                            answer,
                            flags=re.IGNORECASE | re.DOTALL,
                        )
                        section3_match = re.search(
                            r"###\s*3\..*?$",
                            answer,
                            flags=re.IGNORECASE | re.DOTALL,
                        )
                        target_text = "\n".join(
                            s for s in [
                                section2_match.group(0).lower() if section2_match else "",
                                section3_match.group(0).lower() if section3_match else "",
                            ] if s
                        )
                        if not target_text:
                            target_text = answer_lower

                        def has_both_images(prod_row):
                            style_name = str(prod_row.get("Style Image Filename", "")).strip()
                            ing_name = str(prod_row.get("Ingredients Image Filename", "")).strip()
                            style_img = os.path.join("images", style_name)
                            ing_img = os.path.join("images", ing_name)
                            return os.path.exists(style_img) and os.path.exists(ing_img)

                        # 缺圖時回退到同類可用素材（确保你暂时没图也能稳定展示）
                        fallback_slug_map = {
                            "sleep_aid": ["red_musk", "soul_of_shupo"],
                            "suhe_card": ["grand_suhe_incense"],
                            "dragon_phoenix_card": ["qi_lin_blood_resin"],
                            "horse_wealth": ["qi_lin_blood_resin"],
                            "ginseng_lotus": ["fu_yan_nian"],
                            "osmanthus_jasmine_pear": ["midnight_pear_in_the_canopy", "youthful_jasmine"],
                            "sandalwood": ["imperial_dragon_s_breath"],
                            "agarwood": ["imperial_dragon_s_breath"],
                            "epidemic_protection": ["an_gong_niu_huang", "grand_suhe_incense"],
                            "blue_imperial_plum_card": ["lake_blue_imperial_pluim"],
                            "ziwei_talisman": ["seven_fragrances_and_twelve_essences"],
                            "pine_cone": ["the_five_elemental_guardians"],
                            "blessing_comb": ["youthful_jasmine"],
                            "jasmine_lotion": ["youthful_jasmine"],
                        }

                        slug_to_row = {}
                        for _, r in image_df.iterrows():
                            slug_key = str(r.get("English Slug", "")).strip()
                            if slug_key:
                                slug_to_row[slug_key] = r

                        best_product = None
                        best_score = 0

                        # 選擇「最像被推薦的那一款」，只展示該產品兩張圖
                        for _, row in image_df.iterrows():
                            original_name = str(row.get("Original Name", ""))
                            slug = str(row.get("English Slug", ""))

                            split_tokens = re.split(r"[\\/，,、\s()（）\-]+", original_name)
                            keywords = [original_name, slug] + split_tokens
                            keywords = [k.strip().lower() for k in keywords if len(k.strip()) >= 2]

                            score = sum(1 for k in keywords if k in target_text)
                            if score > best_score:
                                best_score = score
                                best_product = row

                        if best_product is not None and best_score > 0:
                            prod = best_product
                            used_fallback = False

                            if not has_both_images(prod):
                                # 先尝试同类映射回退
                                raw_slug = str(prod.get("English Slug", "")).strip()
                                for fb_slug in fallback_slug_map.get(raw_slug, []):
                                    fb_row = slug_to_row.get(fb_slug)
                                    if fb_row is not None and has_both_images(fb_row):
                                        prod = fb_row
                                        used_fallback = True
                                        break

                            if not has_both_images(prod):
                                # 若映射回退仍失败，挑选“可用图片且关键词得分最高”的候选
                                best_available = None
                                best_available_score = 0
                                for _, row in image_df.iterrows():
                                    if not has_both_images(row):
                                        continue
                                    name2 = str(row.get("Original Name", ""))
                                    slug2 = str(row.get("English Slug", ""))
                                    tokens2 = re.split(r"[\\/，,、\s()（）\-]+", name2)
                                    kws2 = [name2, slug2] + tokens2
                                    kws2 = [k.strip().lower() for k in kws2 if len(k.strip()) >= 2]
                                    score2 = sum(1 for k in kws2 if k in target_text)
                                    if score2 > best_available_score:
                                        best_available_score = score2
                                        best_available = row
                                if best_available is not None:
                                    prod = best_available
                                    used_fallback = True

                            if has_both_images(prod):
                                if used_fallback:
                                    st.info(
                                        f"原推荐产品缺图，已自动回退到可展示素材：{prod['Original Name']}"
                                    )
                                st.write(f"✅ **推薦產品視覺素材: {prod['Original Name']}**")
                                c1, c2 = st.columns(2)
                                style_img = f"images/{prod['Style Image Filename']}"
                                ing_img = f"images/{prod['Ingredients Image Filename']}"

                                with c1:
                                    if os.path.exists(style_img):
                                        st.image(style_img, caption=f"{prod['Original Name']} - 款式圖")
                                    else:
                                        st.warning(f"缺少圖片檔案: {prod['Style Image Filename']}")

                                with c2:
                                    if os.path.exists(ing_img):
                                        st.image(ing_img, caption=f"{prod['Original Name']} - 配方功效圖")
                                    else:
                                        st.warning(f"缺少圖片檔案: {prod['Ingredients Image Filename']}")
                            else:
                                st.warning("已匹配产品，但未找到可展示的成套图片。")
                        else:
                            st.info("未檢索到推薦產品，請在第2或第3部分中明确写出产品名称。")
                    else:
                        st.error("找不到 product_image_filenames.csv，請確保檔案已上傳至 docs/ 目錄。")

                    st.session_state.messages.append({"role": "user", "content": user_input})
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    st.error(f"生成失敗: {e}")
