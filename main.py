import os
from pathlib import Path

import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore


BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
RULES_PATH = BASE_DIR / ".cursorrules"


@st.cache_data(show_spinner=False)
def load_docs() -> dict:
    """Load SOP/product docs and local rules as context."""
    docs = {}
    sop_path = DOCS_DIR / "SOP_Flow.md"
    product_path = DOCS_DIR / "Product_Info.md"

    docs["sop"] = sop_path.read_text(encoding="utf-8") if sop_path.exists() else ""
    docs["product"] = product_path.read_text(encoding="utf-8") if product_path.exists() else ""
    docs["rules"] = RULES_PATH.read_text(encoding="utf-8") if RULES_PATH.exists() else ""
    return docs


def build_prompt(docs: dict, customer_message: str) -> str:
    """Build a prompt that enforces .cursorrules output style."""
    sop = docs.get("sop", "")
    product = docs.get("product", "")
    rules = docs.get("rules", "")

    prompt = f"""
你現在扮演「Scent Curator」（冷凝香珠的專屬顧問）。你要像一位高級但友善的朋友，而不是教科書或硬推銷。

下面是內部資料（請完整閱讀並嚴格遵守，尤其是 .cursorrules 的語氣與結構要求）：

=================《SOP_Flow.md》開始=================
{sop}
=================《SOP_Flow.md》結束=================

=================《Product_Info.md》開始=================
{product}
=================《Product_Info.md》結束=================

=================《.cursorrules》開始=================
{rules}
=================《.cursorrules》結束=================

對話中，客戶說的原文如下（英文）：
-----------------
{customer_message}
-----------------

你的任務（嚴格遵守）：

1）SOP 階段判斷 + 痛點（中文，簡短）  
- 根據《SOP_Flow.md》的六階段流程，判斷客戶目前處於哪一個階段。  
- 用中文非常簡短地說明：為什麼是這一階段 + 客戶潛在痛點（對應 Product_Info.md 的矩陣哪一行）+ 推薦哪一個產品。  

2）英文回覆（英文，<= 3 句）  
- 口吻自然、像真人，避免術語堆砌與過度推銷。  
- 必須包含：暖心開場 + 1 個明確推薦（基於 Product_Info.md 的某一個產品）+ 1 句輕柔追問（Gentle Hook）。  
- 避免使用 “Intangible Cultural Heritage” 這類生硬字眼，優先用 “ancient artisan craft / hand-made heritage” 等更自然表述。  
- 避免醫療承諾，用 holistic wellness / botanical aromatherapy 的表達方式。  

輸出格式要求（務必嚴格遵守，方便前端展示）：

只輸出 JSON（不要多任何文字/Markdown/代碼塊），字段如下：
{{
  "stage_zh": "當前客戶所處階段（中文簡稱，例如：第二階段：需求挖掘與價值鋪墊）",
  "analysis_zh": "中文簡短分析：階段判斷依據 + 痛點矩陣匹配 + 推薦產品（簡短、條列也可）",
  "reply_en": "給客戶的英文回覆（最多3句，暖心開場+單一推薦+輕柔追問）"
}}
"""
    return prompt


def _extract_json(text: str) -> dict:
    import json

    try:
        return json.loads(text.strip())
    except Exception:
        # 回退：尝试截取第一个 { 到最后一个 }（兼容模型输出了额外文本）
        s = text.find("{")
        e = text.rfind("}")
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(text[s : e + 1])
            except Exception:
                pass
        raise RuntimeError(f"模型返回内容无法解析为 JSON：\n{text}")


def call_openai(prompt: str, model: str, temperature: float) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if OpenAI is None:
        raise RuntimeError("未安装 openai 库，请先 `pip install openai`。")
    if not api_key:
        raise RuntimeError("未检测到 OPENAI_API_KEY 环境变量。")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a Scent Curator. Output ONLY valid JSON matching the schema.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    content = response.choices[0].message.content or ""
    return _extract_json(content)


def call_anthropic(prompt: str, model: str, temperature: float) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if Anthropic is None:
        raise RuntimeError("未安装 anthropic 库，请先 `pip install anthropic`。")
    if not api_key:
        raise RuntimeError("未检测到 ANTHROPIC_API_KEY 环境变量。")

    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=700,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )

    # anthropic SDK returns a list of content blocks
    parts = []
    for block in getattr(resp, "content", []) or []:
        if getattr(block, "type", None) == "text":
            parts.append(getattr(block, "text", ""))
    content = "\n".join(parts).strip()
    return _extract_json(content)


def call_model(prompt: str, provider: str, model: str, temperature: float) -> dict:
    if provider == "OpenAI":
        return call_openai(prompt, model=model, temperature=temperature)
    if provider == "Anthropic":
        return call_anthropic(prompt, model=model, temperature=temperature)
    raise RuntimeError(f"未知 provider：{provider}")

    return data


def main():
    st.set_page_config(page_title="Scent Curator 营销助手", page_icon="✨", layout="centered")

    st.title("Scent Curator 跨境营销助手")
    st.markdown(
        "读取 `docs/SOP_Flow.md` + `docs/Product_Info.md` 作为知识库，"
        "并严格按 `.cursorrules` 的结构输出：中文（阶段+痛点）+ 英文回复（<=3句）。"
    )

    docs = load_docs()
    if not docs.get("sop") or not docs.get("product"):
        st.error("未找到 `docs/SOP_Flow.md` 或 `docs/Product_Info.md`，請確認文件存在。")
        return

    with st.sidebar:
        st.subheader("模型设置")
        provider = st.radio("Provider", options=["OpenAI", "Anthropic"], horizontal=True)
        default_model = "gpt-4.1-mini" if provider == "OpenAI" else "claude-3-5-sonnet-latest"
        model = st.text_input("Model", value=default_model)
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.3, step=0.05)
        st.caption(
            "OpenAI 需要环境变量 `OPENAI_API_KEY`；Anthropic 需要 `ANTHROPIC_API_KEY`。"
        )

    customer_message = st.text_area(
        "客户对话内容（建议粘贴英文原文）",
        placeholder="粘贴客户的话，例如：Hi, I saw your Instagram. Can you tell me more?",
        height=200,
    )

    if st.button("生成回复", type="primary", use_container_width=True):
        if not customer_message.strip():
            st.warning("請先輸入客戶對話內容。")
            return

        with st.spinner("正在生成中（严格按 .cursorrules 结构输出）..."):
            try:
                prompt = build_prompt(docs, customer_message)
                result = call_model(prompt, provider=provider, model=model, temperature=temperature)
            except Exception as e:
                st.error(f"生成过程出错：{e}")
                return

        stage_zh = result.get("stage_zh", "").strip()
        analysis_zh = result.get("analysis_zh", "").strip()
        reply_en = result.get("reply_en", "").strip()

        st.subheader("[SOP Phase & Analysis]（中文）")
        if stage_zh:
            st.write(f"**阶段**：{stage_zh}")
        if analysis_zh:
            st.write(analysis_zh)
        if not stage_zh and not analysis_zh:
            st.write("（模型未返回中文分析）")

        st.subheader("[English Reply]（English）")
        if reply_en:
            st.write(reply_en)
        else:
            st.write("（模型未返回英文回复）")


if __name__ == "__main__":
    main()

