# 在OCI上執行113年爬蟲

## 1. 在OCI Cloud Shell執行

```bash
# 下載爬蟲腳本
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name scripts/simple-crawler-113.py \
    --file simple-crawler-113.py

# 安裝必要套件
pip3 install --user beautifulsoup4

# 執行爬蟲（建議用screen或tmux）
screen -S crawler113
python3 simple-crawler-113.py 1 2201

# 按 Ctrl+A 然後 D 可以離開screen
# 之後用 screen -r crawler113 可以回到執行畫面
```

## 2. 定期檢查進度

```bash
# 檢查最新的permits.json
oci os object get \
    --namespace nrsdi1rz5vl8 \
    --bucket-name taichung-building-permits \
    --name permits.json \
    --file - | python3 -c "import json,sys; data=json.load(sys.stdin); y113=[p for p in data if isinstance(p,dict) and p.get('indexKey','').startswith('113')]; print(f'113年進度: {len(y113)}/2201 ({len(y113)/2201*100:.1f}%)')"
```

## 3. 查看監控面板

https://objectstorage.ap-tokyo-1.oraclecloud.com/n/nrsdi1rz5vl8/b/taichung-building-permits/o/monitor.html