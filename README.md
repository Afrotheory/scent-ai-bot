# 跨境合香珠營銷助手（Streamlit 版）

本項目提供一個基於 Streamlit 的簡易 Web 界面，幫助你在 WhatsApp 等渠道上快速完成「跨境營銷顧問式回覆」：

- 輸入客戶的英文對話內容
- 自動讀取 `docs/SOP_Flow.md` + `docs/Product_Info.md` 作為知識庫
- 點擊生成後，嚴格按照 `.cursorrules` 的結構輸出：
  - **[SOP Phase & Analysis]（中文）**：階段 + 潛在痛點（對應矩陣）+ 推薦產品（簡短）
  - **[English Reply]（English）**：≤ 3 句、自然口吻、單一推薦 + 輕柔追問

## 1. 安裝依賴

在項目根目錄（包含 `main.py` 的目錄）打開終端，運行：

```bash
pip install -r requirements.txt
```

## 2. 配置 OpenAI 或 Anthropic API 密鑰

本應用支持在側邊欄切換 Provider（OpenAI / Anthropic）。

請在系統環境中設置：

```bash
setx OPENAI_API_KEY "your_api_key_here"
```

或在當前終端臨時設置（Windows PowerShell 示例）：

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

使用 Anthropic 時，請設置：

```bash
setx ANTHROPIC_API_KEY "your_api_key_here"
```

PowerShell 臨時設置：

```powershell
$env:ANTHROPIC_API_KEY="your_api_key_here"
```

## 3. 確保文檔存在

請確認以下文件已存在且內容正確：

- `docs/SOP_Flow.md`
- `docs/Product_Info.md`

`main.py` 會在啟動時自動讀取這兩個文件，作為提示詞上下文。

## 4. 啟動應用

在項目根目錄運行：

```bash
streamlit run main.py
```

瀏覽器打開後，你將看到一個輸入框：

- 將客戶的英文對話粘貼進去
- 點擊「分析對話」
- 界面會顯示：
  - 【[SOP Phase & Analysis]（中文）】
  - 【[English Reply]（English）】

## 5. 自定義與擴展

- 如需更換模型或調整溫度，可修改 `main.py` 中 `call_model` 函數。
- 如需支持其他語言客戶輸入，可在 `build_prompt` 中增加說明，讓模型先判斷/翻譯再分析。

