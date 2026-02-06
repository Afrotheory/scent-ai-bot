import streamlit as st
import google.generativeai as genai

# 页面配置
st.set_page_config(page_title="Scent Curator Assistant", layout="centered")
st.title("🏯 东方香礼跨境营销助手 (Gemini版)")


# 读取本地知识库
def load_docs():
    try:
        with open("docs/SOP_Flow.md", "r", encoding="utf-8") as f:
            sop = f.read()
        with open("docs/Product_Info.md", "r", encoding="utf-8") as f:
            product = f.read()
        return sop, product
    except FileNotFoundError:
        st.error("找不到 docs 文件夹下的文件，请确保已经上传 SOP_Flow.md 和 Product_Info.md")
        return "", ""


sop_content, product_content = load_docs()

# 获取 Gemini API Key (从 Streamlit Secrets 读取)
gemini_key = st.secrets.get("GEMINI_API_KEY")

if not gemini_key:
    st.error("请在 Streamlit Advanced Settings 中配置 GEMINI_API_KEY")
else:
    genai.configure(api_key=gemini_key)
    # 使用 gemini-1.5-flash (速度快且免费额度高)
    model = genai.GenerativeModel("gemini-1.5-flash")

    customer_input = st.text_area(
        "粘贴客户的询盘 (Paste customer query here):",
        placeholder="e.g. Why is it so expensive?",
    )

    if st.button("生成专家回复"):
        if customer_input:
            with st.spinner("Gemini 正在分析 SOP 并组织语言..."):
                prompt = f"""
你是一个专业的香气顾问 (Scent Curator)。

【你的参考资料】
SOP流程:
{sop_content}

产品信息:
{product_content}

【执行要求】
1. 严格遵守 SOP 流程判断阶段。
2. 分析客户潜在痛点。
3. 生成一段地道、优雅、简短的英文回复。
4. 内部分析用中文，回复客户用英文。

【客户当前的话】
{customer_input}
"""

                try:
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"发生错误: {e}")
        else:
            st.warning("请先输入客户内容")

