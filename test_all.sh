#!/bin/bash
# AutoQuant 一键测试脚本

set -e  # 遇到错误立即退出

echo "================================"
echo "AutoQuant 完整测试套件"
echo "================================"
echo ""

# 激活虚拟环境
source venv/bin/activate

# 1. 单元测试
echo "📋 [1/3] 运行单元测试..."
echo "--------------------------------"
pytest -v --tb=short
echo ""

# 2. 快速回测
echo "📊 [2/3] 运行快速回测 (30天)..."
echo "--------------------------------"
python prepare.py run --mode fast
echo ""

# 3. 因子分析
echo "🔬 [3/3] 运行因子IC分析..."
echo "--------------------------------"
python research.py --mode fast 2>&1 | grep -A 15 "Factor IC Ranking" || true
echo ""

# 总结
echo "================================"
echo "✅ 所有测试完成！"
echo "================================"
echo ""
echo "如需更多测试："
echo "  - 完整回测: python prepare.py run --mode full"
echo "  - 多市场验证: python research.py --multi-market --mode fast"
echo "  - MA参数优化: python research.py --optimize MA --mode fast"
