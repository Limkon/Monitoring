Keep Active GitHub Actions Workflow
此倉庫使用 GitHub Actions 工作流來管理和更新兩個不同倉庫（A 和 B）中的 webs/ 目錄。工作流定期運行，重新生成 webs/ 目錄的內容，檢查文件數量是否超過限制，並進行必要的清理和更新。

工作流概述
A 倉庫：當前運行代碼的倉庫。

B 倉庫：目標倉庫，webs/ 目錄會被同步到此倉庫。

工作流行為
檢查 webs/ 目錄：
工作流檢查 A 倉庫 中 webs/ 目錄的文件數量。如果文件數量超過 5 個，則會清空該目錄。

重新生成 webs/ 目錄：
工作流運行 Python 腳本 (bludweb.py) 來重新生成 webs/ 目錄中的內容。

推送更新至 A 倉庫：
工作流將 webs/ 目錄的更新提交並推送回 A 倉庫。

同步至 B 倉庫：
工作流同時克隆 B 倉庫，複製 webs/ 目錄並將更新的內容推送到 B 倉庫。

設置說明
Secrets 配置： 為了確保工作流能順利運行，您需要配置以下 GitHub Secrets：

PAT：帶有 repo 權限的 Personal Access Token（PAT），用於推送到 B 倉庫。

USER：您的 GitHub 用戶名（或組織名稱）。

REPO：B 倉庫 的名稱（目標倉庫）。

這些 secrets 是用來認證並推送變更到 B 倉庫。

Python 依賴項： 工作流使用 Python，並且需要安裝依賴項。所需的依賴包括：

jinja2

python-dotenv

bludweb.py 腳本依賴於這些包，因此在工作流中會自動安裝這些依賴。

工作流觸發
工作流可以通過兩種方式觸發：

定時觸發：
它會根據 cron 調度每 15 天運行一次：0 0 */15 * *。

手動觸發：
您也可以使用 workflow_dispatch 事件手動觸發工作流。

工作流運作方式
1. 檢出當前倉庫 (A 倉庫)
工作流使用 actions/checkout 動作來檢出當前倉庫。並設置 persist-credentials: true，確保使用默認的 GitHub token 來推送更改至 A 倉庫。

2. 設置 Python 環境
工作流設置 Python 並安裝必要的依賴項 (jinja2, python-dotenv) 以運行 Python 腳本。

3. 檢查並清理 A 倉庫中的 webs/ 目錄
工作流檢查 webs/ 目錄中的文件數量。如果超過 5 個，會清空該目錄。

4. 重新生成 webs/ 目錄
bludweb.py 腳本會執行並重新生成 webs/ 目錄中的內容。

5. 提交並推送至 A 倉庫
重新生成文件後，工作流會將更改提交並推送回 A 倉庫。

6. 同步至 B 倉庫
工作流會克隆 B 倉庫，複製更新的 webs/ 目錄，並將更改推送至 B 倉庫。

目錄結構
bash
複製
編輯
.
├── .github/
│   └── workflows/
│       └── keep_active.yml  # GitHub Actions 工作流
├── templates/
│   └── bludweb.py           # 重新生成 webs 目錄的 Python 腳本
└── webs/                     # 生成的內容將保存在這裡
示例用例
此工作流適用於需要定期重新生成並同步 webs/ 目錄的情況。例如：

A 倉庫 可能是中心倉庫，其中的內容會定期更新，而 B 倉庫 可能是需要最新靜態文件的部署倉庫。

故障排除
推送時出現 403 錯誤：
這通常是由於 Personal Access Token (PAT) 所屬的用戶沒有足夠的權限推送到目標倉庫。請確保 PAT 具有 repo 權限，並且用戶對 B 倉庫 具有推送權限。

找不到目錄：
請確保 webs/ 目錄在兩個倉庫中都存在。如果不存在，請手動創建該目錄，或者根據需要調整工作流以處理目錄缺失的情況。

