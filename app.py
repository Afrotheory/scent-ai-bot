import streamlit as st
import google.generativeai as genai

# 页面配置
st.set_page_config(page_title="Scent Curator Assistant", layout="centered")
st.title("🏯 东方香礼跨境营销助手 (Gemini版)")


# 读取本地知识库
def load_docs():
    try:
        # 使用 utf-8 确保中文不乱码
        with open("docs/SOP_Flow.md", "r", encoding="utf-8") as f:
            sop = f.read()
        with open("docs/Product_Info.md", "r", encoding="utf-8") as f:
            product = f.read()
        return sop, product
    except Exception as e:
        st.error(f"读取文档失败: {e}")
        return "", ""


sop_content, product_content = load_docs()

# 获取 Gemini API Key
gemini_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_key:
    st.error("请在 Streamlit Secrets 中配置 GEMINI_API_KEY")
else:
    genai.configure(api_key=gemini_key)

    # 【核心修复逻辑】：自动检测可用模型并選擇合適的名稱
    try:
        # 1. 自動獲取可用模型列表，只保留支持 generateContent 的
        available_models = [
            m.name
            for m in genai.list_models()
            if "generateContent" in getattr(m, "supported_generation_methods", [])
        ]

        # 2. 優先選擇包含 'gemini-1.5-flash' 的模型，否則退回第一個可用模型
        target_model = next(
            (m for m in available_models if "gemini-1.5-flash" in m), None
        )
        if not target_model:
            target_model = available_models[0] if available_models else "models/gemini-1.5-flash"

        model = genai.GenerativeModel(model_name=target_model)
        # st.success(f"已成功加载模型: {target_model}")  # 如需調試可打開
    except Exception as e:
        st.error(f"无法获取模型列表，请检查 API Key 是否有效: {e}")
        # 保底方案：仍嘗試使用通用名稱
        model = genai.GenerativeModel("gemini-1.5-flash")

    customer_input = st.text_area(
        "粘贴客户的询盘 (Paste customer query here):",
        placeholder="e.g. Why is it so expensive?",
    )

    if st.button("生成专家回复"):
        if customer_input:
            with st.spinner("Gemini 正在分析 SOP 并组织语言..."):
                # 构建 Prompt（强硬指令版）
                prompt = f"""
                You are a Scent Curator for Cold-Infused Incense. 
                Your goal: Sound like a sophisticated, helpful friend. 
                
                【Rules】
                1. CONCISE: Keep English replies under 3 sentences. 
                2. HUMAN-LIKE: No jargon. Use "Actually...", "I think you'll love...".
                3. STRUCTURE: You MUST provide the response in exactly this format:
                
                [SOP阶段 & 痛点分析]
                (这里用中文简短分析：阶段+痛点)
                
                ---
                
                [English Reply]
                (Here is your warm, short, 1-3 sentence response in English)

                【Context】
                SOP: {sop_content}
                Products: {product_content}

                【Customer Message】
                {customer_input}
                """

                try:
                    response = model.generate_content(prompt)
                    # 这样可以让结果显示得更漂亮
                    st.subheader("💡 处理建议")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"发生错误: {e}")
        else:
            st.warning("请先输入客户内容")

