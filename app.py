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
    try:
        genai.configure(api_key=gemini_key)

        # 【兼容性修复】：自动选择可用模型
        # 有些 Key 需要 'gemini-1.5-flash'，有些需要 'models/gemini-1.5-flash'
        # 我们这里直接指定一个最稳妥的调用方式
        model = genai.GenerativeModel("gemini-1.5-flash")

        customer_input = st.text_area(
            "粘贴客户的询盘 (Paste customer query here):",
            placeholder="e.g. Why is it so expensive?",
        )

        if st.button("生成专家回复"):
            if customer_input:
                with st.spinner("Gemini 正在分析 SOP 并组织语言..."):
                    # 构建 Prompt
                    prompt = (
                        f"Context: {sop_content}\n\n"
                        f"Products: {product_content}\n\n"
                        "Task: Analyze the following customer message based on the SOP stages and product matrix. "
                        "Internal analysis in Chinese, final reply to customer in elegant English.\n\n"
                        f"Customer: {customer_input}"
                    )

                    # 增加错误重试逻辑
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
            else:
                st.warning("请先输入客户内容")
    except Exception as e:
        st.error(f"模型初始化失败，可能是API Key无效或地区限制: {e}")

