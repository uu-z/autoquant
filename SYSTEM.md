# AutoQuant - 专业量化系统

## 系统架构

```
Alpha 发现 → 回测验证 → 风险分析 → 实盘测试
    ↓           ↓           ↓           ↓
 因子挖掘    样本外测试   压力测试    小资金验证
```

## 核心模块

### 1. 因子库 (`factors.py`)
- **标准化接口**：所有因子继承 `Factor` 基类
- **IC 评估**：`factor.ic(df)` 计算信息系数
- **可组合**：`FactorCombiner` 支持加权/投票

**内置因子**：
- `MACrossover`: 均线交叉
- `RSIFilter`: RSI 超买超卖
- `MomentumFilter`: 价格动量
- `BollingerBands`: 布林带均值回归
- `VolatilityFilter`: ATR 波动率过滤

### 2. 研究工具 (`research.py`)
```bash
# 因子 IC 分析
python research.py analyze --mode full

# 参数网格搜索
python research.py optimize

# 构建因子组合
python research.py ensemble
```

### 3. 回测引擎 (`prepare.py`)
- **真实成本**：Binance 费用 + 市场冲击
- **样本外验证**：Walk-forward 分割
- **多币种测试**：`--symbol ETH/USDT`

### 4. 策略实现 (`strategy.py`)
- **因子驱动**：基于 IC 分析选择因子
- **自适应**：根据连胜/连败调整仓位
- **模块化**：易于替换因子组合

---

## 工作流程

### Phase 1: 因子发现
```bash
# 1. 分析所有候选因子
python research.py analyze --mode full

# 输出示例：
# === Factor IC Ranking ===
#   RSI_14_65_35: IC=0.077
#   MA_15_60: IC=0.064
#   Momentum_10_0.03: IC=-0.070
```

### Phase 2: 参数优化
```bash
# 2. 网格搜索最佳参数
python research.py optimize

# 输出：
# Best params: fast=15, slow=60, IC=0.064
```

### Phase 3: 组合构建
```bash
# 3. 构建因子组合
python research.py ensemble

# 输出：
# Ensemble IC: 0.15 (> individual factors)
```

### Phase 4: 回测验证
```bash
# 4. 训练集测试
python prepare.py run --mode fast
# Score: 1.258

# 5. 样本外验证
python prepare.py validate --mode fast
# Score: 1.937 (泛化良好 ✓)

# 6. 多币种测试
python prepare.py run --symbol ETH/USDT
# Score: -1.580 (需改进)
```

---

## 当前性能

| 指标 | BTC 训练 | BTC 验证 | ETH 测试 |
|------|----------|----------|----------|
| Score | 1.258 | 1.937 ✓ | -1.580 ✗ |
| Sharpe | 2.33 | 3.64 | -3.14 |
| Drawdown | 6.3% | 4.6% | 11.2% |
| Win Rate | 57% | 67% | 12% |
| Trades | 14 | 5 | 16 |

**结论**：
- ✅ BTC 泛化良好（验证 > 训练）
- ✗ ETH 泛化失败（需多市场因子）

---

## 对比专业水平

| 维度 | 当前 | 专业 | 完成度 |
|------|------|------|--------|
| 因子库 | 5 个基础因子 | 100+ 因子 | 5% |
| IC 分析 | ✅ 已实现 | ✅ | 100% |
| 样本外验证 | ✅ Walk-forward | ✅ | 100% |
| 真实成本 | ✅ 费用+滑点 | ✅ | 100% |
| 参数优化 | 网格搜索 | 贝叶斯优化 | 50% |
| 多市场 | 单币种优化 | 跨市场泛化 | 30% |
| 风控 | 基础仓位管理 | 多层风控 | 40% |
| 实盘 | ❌ | ✅ | 0% |

---

## 下一步

### 立即可做
1. **多市场因子**：在 BTC+ETH 上同时优化
2. **因子正交化**：去除因子间相关性
3. **动态权重**：根据市场状态调整因子权重

### 中期目标
1. **机器学习**：XGBoost 预测因子权重
2. **高频因子**：订单簿、资金费率
3. **执行优化**：TWAP/VWAP 算法

### 长期规划
1. **实盘系统**：WebSocket 接入
2. **监控告警**：Grafana 仪表盘
3. **分布式回测**：Ray 并行加速

---

## 使用指南

### 快速开始
```bash
# 1. 分析因子
python research.py analyze

# 2. 运行回测
python prepare.py run --mode fast

# 3. 验证泛化
python prepare.py validate --mode fast
```

### AI 自主实验
```bash
# 修改 strategy.py 中的因子组合
# 例如：添加新因子、调整权重、改变组合方法
git commit -m "test new factor combination"
python prepare.py validate --mode fast
```

### 最佳实践
1. **始终用 IC 指导**：只使用 |IC| > 0.05 的因子
2. **强制样本外验证**：验证分数 < 0 直接丢弃
3. **多市场测试**：至少在 2 个币种上测试
4. **简单优先**：2-3 个因子组合优于 5+ 个

---

## 文件说明

```
autoquant/
├── factors.py       # 因子库（标准化接口）
├── research.py      # 研究工具（IC 分析、优化）
├── prepare.py       # 回测引擎（只读）
├── strategy.py      # 策略实现（AI 可修改）
├── program.md       # AI 指令
└── results.tsv      # 实验日志
```

---

## 关键改进

**之前**：
- 手动调参，盲目优化
- 无因子评估，过拟合严重
- 训练 1.899 → 验证 -0.453

**现在**：
- IC 驱动，科学选因子
- 样本外验证，防过拟合
- 训练 1.258 → 验证 1.937 ✓

**核心差异**：
```python
# 之前：手动调参
ma_fast = 17  # 为什么是 17？
ma_slow = 53  # 为什么是 53？

# 现在：IC 驱动
factor = MACrossover(15, 60)  # IC=0.064
factor.ic(df)  # 可验证预测能力
```
