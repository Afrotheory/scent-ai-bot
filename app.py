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
                        ["🔍 診斷模式 (Diagnosis)", "✍️ 創作模式 (Creative/Translation)", "📊 產品導航表"])
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
    # 模式 3：全自動產品導航表 (對接優化後的 CSV)
    elif mode == "📊 產品導航表":
        st.header("📊 全品類中英對照及官方報價單")

        csv_path = "docs/Price_List_Optimized.csv"
        if os.path.exists(csv_path):
            df_full = pd.read_csv(csv_path)

            # 搜尋與過濾功能
            search_q = st.text_input("🔍 搜尋產品名稱、規格或功效:", "")
            if search_q:
                df_display = df_full[
                    df_full.astype(str).apply(
                        lambda x: x.str.contains(search_q, case=False)
                    ).any(axis=1)
                ]
            else:
                df_display = df_full

            st.dataframe(df_display, use_container_width=True, hide_index=True)

            st.success(f"✅ 已加載全部 {len(df_full)} 條價格數據")
        else:
            st.error("找不到 Price_List_Optimized.csv，請確認已上傳。")

        st.divider()
        st.subheader("📏 尺寸及手圍佩戴建議")
        st.markdown(lib.get("sizes", "未找到尺寸表"))

        user_input = ""
        mode_instruction = ""

    if mode != "📊 產品導航表" and st.button("🚀 生成專家方案", type="primary"):
        if not user_input:
            st.warning("請輸入內容。")
        else:
            # --- 根據模式動態生成指令 (加入尺寸專業話術) ---
            if mode.startswith("🔍 診斷模式"):
                mode_logic = f"""
                TASK: DIAGNOSTIC_ANALYSIS
                1. SOP & TCM: Identify stage from {lib['sop']} and syndrome from {lib['tcm']}.
                2. SIZE EXPERT: If beads are mentioned, explain that larger beads (14mm/18mm) occupy more internal space, making the fit tighter than smaller beads.
                3. CLOSING: Always suggest offering 2 spare beads to ensure a perfect fit.
                """
            else:
                mode_logic = f"""
                TASK: CREATIVE_TRANSLATION
                1. TCM & STYLE: Use {lib['tcm']} for logic and maintain an imperial, elegant tone.
                2. OBJECTION HANDLING: Proactively address wrist size concerns. Mention that we provide 2 complimentary spare beads and explain the "Internal Space" logic for larger beads.
                """

            system_instruction = f"""
            You are a "Master Scent Therapist." 
            {mode_logic}

            【Library Reference】
            - Products/Prices: {lib['prices']} 
            - Precise Sizes & Counts: {lib['sizes']} (Note: 10mm=20pcs, 14mm=16pcs, 18mm=13pcs)

            【Professional Phrases to Integrate】
            - "Since 18mm beads are bolder and thicker, they occupy more internal space on the wrist."
            - "To ensure a perfect fit, we include 2 complimentary spare beads and a professional elastic cord in your package."
            - "This allows you to customize the tension for your ultimate comfort."

            【Output Rules】
            - Section 2 MUST be: ### 2. 建議英文回覆 (Mentor's Reply)
            - Section 3 MUST be: ### 3. 中文參考 (Translation)
            - English must be 1-3 sentences, elegant, and warm.
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
                        stopwords = {
                            "the", "and", "for", "with", "from", "into", "this", "that",
                            "of", "in", "to", "a", "an", "is", "on", "by", "or",
                        }

                        # 明确别名优先（避免“孔韻迷迭”这类推荐被通用词干扰）
                        direct_alias_map = {
                            "confucian_charm_rosemary": [
                                "孔韻迷迭", "孔韵迷迭", "kong yun mi die",
                                "confucius rosemary", "confucian charm rosemary", "confucian charm",
                            ],
                            "soul_of_shupo": ["蜀魄", "泣血蜀魄", "烈火蜀魄", "soul of shupo", "shupo"],
                            "qi_lin_blood_resin": ["麒麟竭", "龙瑞", "龍瑞", "dragon's blood", "qi lin blood"],
                            "imperial_dragon_s_nectar": ["黑龍涎", "黑龙涎", "imperial black dragon nectar"],
                            "white_dragon_s_realm": ["白龍涎", "白龙涎", "white dragon"],
                            "red_musk": ["紅麝", "红麝", "四合香", "red musk", "four-in-one"],
                            "an_gong_niu_huang": ["安宮牛黃", "安宫牛黄", "an gong niu huang"],
                            "fu_yan_nian": ["傅延年", "fu yan nian"],
                            "the_jiaofang": ["漢宮椒房", "汉宫椒房", "jiaofang"],
                        }

                        for slug_key, aliases in direct_alias_map.items():
                            if any(alias.lower() in target_text for alias in aliases):
                                row = slug_to_row.get(slug_key)
                                if row is not None:
                                    best_product = row
                                    best_score = 999  # 直接命中优先级最高
                                    break

                        # 選擇「最像被推薦的那一款」，只展示該產品兩張圖
                        if best_score < 999:
                            for _, row in image_df.iterrows():
                                original_name = str(row.get("Original Name", ""))
                                slug = str(row.get("English Slug", ""))

                                split_tokens = re.split(r"[\\/，,、\s()（）\-]+", original_name)
                                keywords = [k.strip().lower() for k in ([original_name, slug] + split_tokens) if len(k.strip()) >= 2]
                                keywords = [k for k in keywords if k not in stopwords and len(k) >= 3]

                                # 加权打分：完整命中 > slug 命中 > 关键词命中
                                score = 0
                                if original_name.lower() in target_text:
                                    score += 8
                                if slug.lower() in target_text:
                                    score += 8
                                score += sum(1 for k in keywords if k in target_text)

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
                                    kws2 = [k.strip().lower() for k in ([name2, slug2] + tokens2) if len(k.strip()) >= 2]
                                    kws2 = [k for k in kws2 if k not in stopwords and len(k) >= 3]
                                    score2 = 0
                                    if name2.lower() in target_text:
                                        score2 += 8
                                    if slug2.lower() in target_text:
                                        score2 += 8
                                    score2 += sum(1 for k in kws2 if k in target_text)
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
