## 專案結構

```
test/
├── main.py                   # 主程式進入點
├── config/                   # 設定檔目錄
│   └── configuration.json    # 範例設定檔
├── src/                      # 原始碼目錄
│   ├── experiment.py         # 實驗執行器
│   ├── logger.py             # 日誌管理模組
│   ├── topology.py           # 拓撲管理模組
│   ├── algorithm.py          # 演算法管理模組
│   ├── traffic.py            # 流量管理模組
│   ├── config.py             # 設定管理模組
│   └── failure.py            # 故障管理模組
└── README.md                 # 說明文件
```

## 模組功能說明

### 1. 設定管理（config.py）
- 讀取與管理 JSON 設定檔
- 檔案操作

### 2. 日誌管理（logger.py）
- 支援時間與狀態記錄
- 檔案日誌輸出

### 3. 拓撲管理（topology.py）
- Mininet 網路拓撲建構
- 主機與交換器管理
- 連線狀態檢查

### 4. 演算法管理（algorithm.py）
- 故障恢復演算法

### 5. 流量管理（traffic.py）
- iperf 流量產生
- 流量監控與資料收集

### 6. 故障管理（failure.py）
- 連結故障模擬
- 故障偵測與恢復

### 7. 實驗執行器（experiment.py）
- 整合所有模組功能
- 實驗流程控制

## 使用方式

### 1. 設定檔建立

請在 `config/` 目錄下建立設定檔，例如 `configuration.json`：

```json
{
    "UserName": "lce",
    "OutputFile": "single_link_failure_result_data.pkl",
    "SaveTraceFile": "True",
    "FailureMode": "single",
    "Mode": "fixed",
    "Algorithm": ["SDFFR_MP", "SDFFR_MP_LB"],
    "Vertex": [20],
    "Edge": [35],
    "LinkBandwidth": [1000],
    "Throughput": [10],
    "TrafficModel": [1],
    "ControlPlaneDelay": [20],
    "FlowCount": [30],
    "Trial": [1, 2],
    "LinkChangeTime": [5],
    "Metric": ["Throughput", "TOTALPacketLoss", "PacketLoss", "RecoveryDelay"]
}
```

### 2. 執行實驗

```bash
# 執行實驗
python3 main.py run configuration1

# 清理實驗環境
python3 main.py clean configuration1
```


### 3. 設定參數說明

- `UserName`: 使用者名稱
- `FailureMode`: 故障模式（single/multiple）
- `Mode`: 遮擋模式 (markov/fixed)
- `Algorithm`: 測試的演算法列表
- `Vertex`: 節點數量
- `Edge`: 鏈路數量
- `LinkBandwidth`: 連結頻寬
- `Throughput`: 流量吞吐量
- `TrafficModel`: 流量模型
- `ControlPlaneDelay`: 控制平面延遲
- `FlowCount`: 流數量
- `Trial`: 實驗次數範圍
- `LinkChangeTime`: 鏈路變動時間間隔
- `Metric`: 評估用指標

## 實驗流程

1. **環境建置**：初始化實驗環境與目錄結構
2. **拓撲建構**：建立 Mininet 網路拓撲
3. **演算法部署**：在 ONOS 控制器上部署故障恢復演算法
4. **流量產生**：使用 iperf 產生測試流量
5. **故障注入**：模擬連結故障與恢復
6. **資料收集**：收集與紀錄
7. **結果分析**：分析實驗結果並儲存

目前程式只能完成第1.2項