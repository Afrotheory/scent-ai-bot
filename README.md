# 跨境合香珠營銷助手（Streamlit + Gemini 版）

本項目提供一個基於 **Streamlit + Google Gemini** 的簡易 Web 界面，幫助你在 WhatsApp、Instagram DM 等場景下，快速完成「Scent Curator 顧問式回覆」：

- 在頁面輸入客戶的英文詢問  
- 自動讀取 `docs/SOP_Flow.md` 和 `docs/Product_Info.md` 作為知識庫  
- 調用 Gemini 模型，根據 SOP 流程輸出：  
  - 用中文做內部階段判斷與痛點分析  
  - 用英文給出地道、優雅的短句回覆（發給客戶用）  

目前主入口文件為 `app.py`（Gemini 版），原先的 `main.py`（OpenAI/Anthropic 版）可作為備選實現保留。

---

## 1. 安裝依賴

在項目根目錄（包含 `app.py` 的目錄）打開終端，運行：

```bash
pip install -r requirements.txt
```

`requirements.txt` 內容：

```txt
streamlit
google-generativeai
```

---

## 2. 配置 Gemini API Key

本項目使用 `google-generativeai` 調用 Gemini 模型，API Key 通過 **Streamlit Secrets** 傳入。

1. 在本地開發時，可以在 `.streamlit/secrets.toml`（需自行創建目錄和文件）中寫入：

   ```toml
   GEMINI_API_KEY = "your_gemini_api_key_here"
   ```

2. 或者在 Streamlit Cloud / 其他部署平台上，在對應的 **Secrets / Environment** 配置界面中新增：

   - Key：`GEMINI_API_KEY`  
   - Value：你的 Gemini API 金鑰

`app.py` 中會通過：

```python
gemini_key = st.secrets.get("GEMINI_API_KEY")
```

自動讀取該值。

---

## 3. 確保文檔存在

請確認以下文件已存在且內容正確（作為模型的提示詞上下文）：

- `docs/SOP_Flow.md`：跨境私域營銷 SOP，包含六階段轉化流程與術語規則  
- `docs/Product_Info.md`：產品資料庫與「痛點-產品」矩陣  

`app.py` 會在啟動時自動讀取這兩個文件。

---

## 4. 啟動 Gemini 版應用

在項目根目錄運行：

```bash
streamlit run app.py
```

瀏覽器打開後，你將看到：

- 一個多行輸入框，用於粘貼客戶詢盤（英文為主）  
- 一個「生成專家回覆」按鈕  

點擊按鈕後，後端會：

1. 讀取 `SOP_Flow.md` + `Product_Info.md`  
2. 組合為一個完整 prompt 傳給 **Gemini 1.5 Flash**  
3. 讓模型：  
   - 先用中文在內部完成 SOP 階段判斷與痛點分析  
   - 再輸出一段簡短、自然的英文回覆（給客戶）  

頁面會直接展示模型返回的內容。

---

## 5. 自定義與擴展建議

- **調整模型 / 風格**：  
  在 `app.py` 中可以將 `gemini-1.5-flash` 替換為其他 Gemini 型號，或在 prompt 中微調語氣與長度。

- **結構化輸出**：  
  如需強制分出「中文分析區 + 英文回覆區」，可以在 prompt 中要求模型使用固定標題或 JSON 結構，再在前端對結果做解析與分塊展示。

- **多輪對話 / 記憶**：  
  可以在 `app.py` 中使用 `st.session_state` 保留歷史對話，構造更長的上下文交給 Gemini，做出貼近「持續顧問」的體驗。

