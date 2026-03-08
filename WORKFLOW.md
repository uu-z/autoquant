# Quant Research Workflow

真实量化研究工作流：研究 → 验证 → 部署

## 1. 因子研究 (research.py)

### IC 分析
```bash
# 单市场分析
python research.py --mode fast

# 多市场验证 (BTC/ETH/SOL)
python research.py --multi-market
```

输出：因子 IC 排名，选择 |IC| > 0.05 的因子

### 参数优化
```bash
# MA 参数网格搜索
python research.py --optimize MA --mode fast
```

输出：最优参数组合

## 2. 策略部署 (strategy.py)

将研究结果写入 `strategy.py`：

```python
self.factors = [
    MACrossover(15, 50),  # IC=0.08
    RSIFilter(14, 65, 35),  # IC=0.07
]
```

## 3. 回测验证 (backtest.py)

```bash
# 快速验证
python backtest.py --mode fast

# 完整回测
python backtest.py
```

## 4. 市场状态检测 (regime.py)

可选：根据市场状态调整策略

```python
from regime import TrendingRegime

regime = TrendingRegime(ma_window=50)
df['is_trending'] = regime.detect(df)

# 在 strategy.py 中使用
if df['is_trending'].iloc[-1]:
    # 趋势策略
else:
    # 震荡策略
```

## 核心原则

1. **IC 驱动**：只用 IC > 0.05 的因子
2. **多市场验证**：因子必须在 BTC/ETH/SOL 上都有效
3. **参数稳定性**：最优参数附近应该有平台区
4. **简单优先**：单因子 > 因子组合

## 文件职责

- `prepare.py` - 数据获取 + 指标计算
- `factors.py` - 因子库 (IC 计算)
- `research.py` - IC 分析 + 参数优化
- `strategy.py` - 策略实现 (使用验证过的因子)
- `backtest.py` - 回测引擎
- `regime.py` - 市场状态检测 (可选)
