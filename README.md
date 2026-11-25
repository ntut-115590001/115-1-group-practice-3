# 115-1-group-practice-3 · 課表系統 v1.1

## 執行系統

使用 Python 3.12 或更新版本，在包含 start.py 的目錄執行 `python start.py`。程式使用 Python 標準函式庫。輸入 `help schedule_search` 可查詢 F7 語法，輸入 `exit` 離開。

## F7 多條件最佳課表搜尋

    schedule_search 必修 候選 最低學分 最高學分 [禁止時段 [偏好選修 [集中節次 [權重]]]]

課號與禁止時段清單用逗號分隔，空清單填 `-`。星期為 1–7，節次為 1–9、a、b、c。一門課的所有上課時段都要出席。重複課號只計一次，兩份課程清單中重疊的課程視為必修。偏好課號須來自有效候選選修。

搜尋依當下課程資料與已選人數，列出每個包含全部必修、總學分介於上下限（含端點）、未額滿、不衝堂且避開禁止時段的組合。結果列出課號、總學分及分數，以精確分數遞減排序，同分以排序後的課號序列遞增排列。沒有可行組合時顯示「無可行課表」。搜尋只產生推薦，學生仍可自行決定是否選課。

### 從空資料開始試跑

依序在系統的 `>` 提示符號後輸入。若已有同名測試課程，可直接使用既有資料或在新解壓的目錄練習。

    course_add R 必修課 2 Lin 12@R101 10
    course_add A 同日選修 2 Lin 13@R101 10
    course_add B 偏好選修 2 Lin 22@R102 10
    schedule_search R A,B 4 4 - B
    schedule_search R A,B 4 4 - B 2-6 2,3,5,2,6

第一個查詢得到 A,R（−10 分）、B,R（−14 分）。第二個查詢得到 B,R（2 分）、A,R（−2 分）。

### 評分

分數 = −10 × 到校天數 − 3 × 空堂節數 − 5 × 早八天數 − 2 × 集中區間外節數 + 6 × 偏好比例。

* 空堂為同一天首末堂之間未排課的節數。早八為第 1 節。
* 集中區間預設第 2–6 節，含端點；每一節落在區間外的課都計一次。
* 偏好比例為「已選偏好選修門數 / 已選選修門數」。未選任何選修時比例為 0。
* 五個係數可傳入非負整數，設為 0 便忽略該項偏好。分數可為負，顯示至小數點後兩位。

## 測試與 TDD 紀錄

在專案根目錄開啟終端機，執行下列指令。

    python -m unittest discover -v
    python -m unittest test.test_f7 -v

若要重現 F7 的敘述及分支覆蓋率，可另外安裝 coverage。

    python -m pip install coverage
    python -m coverage run --branch --include="*/src/optimal_schedule.py" -m unittest discover -v
    python -m coverage report -m

`test/test_f7.py` 是 F7 的驗收測試。`docs/tdd/` 包含 Red、Green 與 Refactor 的原始執行輸出。
