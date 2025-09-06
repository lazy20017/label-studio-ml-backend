# 🔄 智能模型切换功能

## 📋 功能概述

ML后端现在支持智能模型切换，当当前模型连续失败3次时，会自动切换到下一个可用的备用模型，确保标注服务的高可用性。

## 🎯 配置的模型列表

按优先级排序的可用模型：

1. **🥇 主力模型**: `Qwen/Qwen3-30B-A3B-Instruct-2507` - 最新Qwen3，性能最优
2. **🥈 备用模型1**: `Qwen/Qwen2.5-72B-Instruct-GGUF` - 大参数量模型
3. **🥉 备用模型2**: `Qwen/Qwen2.5-32B-Instruct` - 中等参数量，平衡性能
4. **🏅 备用模型3**: `Qwen/Qwen2.5-14B-Instruct` - 小参数量，响应快速
5. **💼 备用模型4**: `Qwen/Qwen2-72B-Instruct` - 前一代大模型
6. **⚡ 备用模型5**: `Qwen/Qwen2-57B-A14B-Instruct` - 平衡性能模型

## 🔧 切换机制

### 触发条件
- **连续失败阈值**: 3次
- **失败类型**: API调用异常、返回空内容、连接失败等

### 切换策略
- **顺序切换**: 按预定义顺序依次尝试模型
- **循环模式**: 所有模型尝试完后回到第一个模型
- **失败记录**: 记录每个模型的历史失败次数

### 重试机制
- **每模型重试**: 切换前每个模型最多重试2次
- **总体策略**: 先重试当前模型，再切换到下一个

## 📊 监控和日志

### 实时状态显示
```
🤖 模型使用情况:
   当前模型: Qwen/Qwen3-30B-A3B-Instruct-2507
   当前失败次数: 0/3
   可用模型: 6 个
     🎯 Qwen3-30B-A3B-Instruct-2507
     💤 Qwen2.5-72B-Instruct-GGUF
     💤 Qwen2.5-32B-Instruct
     💤 Qwen2.5-14B-Instruct
     💤 Qwen2-72B-Instruct
     💤 Qwen2-57B-A14B-Instruct
```

### 切换日志示例
```
❌ 模型 Qwen/Qwen3-30B-A3B-Instruct-2507 连续失败: 3/3
🔄 模型切换: Qwen/Qwen3-30B-A3B-Instruct-2507 → Qwen/Qwen2.5-72B-Instruct-GGUF
📊 切换原因: 连续失败 3 次
```

## ⚙️ 自定义配置

### 修改模型列表
在 `model.py` 的 `setup()` 方法中修改 `available_models` 列表：

```python
self.available_models = [
    "your/primary-model",      # 主力模型
    "your/backup-model-1",     # 备用模型1
    "your/backup-model-2",     # 备用模型2
    # 添加更多模型...
]
```

### 调整切换参数
```python
self.max_model_failures = 3        # 连续失败阈值（默认3次）
max_retries_per_model = 2          # 每模型重试次数（默认2次）
```

## 🔍 API接口

### 获取模型状态
```python
model_status = ml_backend.get_model_status()
# 返回：
{
    "current_model": "Qwen/Qwen3-30B-A3B-Instruct-2507",
    "current_model_index": 0,
    "consecutive_failures": 0,
    "max_failures": 3,
    "available_models": [...],
    "failure_history": {...}
}
```

## 💡 最佳实践

### 模型选择原则
1. **主力模型**: 选择性能最优的最新模型
2. **备用模型**: 按参数量和稳定性降序排列
3. **多样化**: 包含不同系列的模型以提高容错能力

### 监控建议
1. **定期检查**: 关注模型失败历史和切换频率
2. **性能评估**: 对比不同模型的标注质量
3. **及时调整**: 根据实际情况调整模型顺序

## 🛠️ 故障排除

### 常见问题
1. **所有模型都失败**: 检查API密钥和网络连接
2. **频繁切换**: 可能需要调整失败阈值或模型列表
3. **性能下降**: 备用模型可能性能较低，属于正常现象

### 调试方法
1. 查看详细日志了解失败原因
2. 使用 `get_model_status()` 获取实时状态
3. 手动测试单个模型的可用性

---

**🎉 智能模型切换让您的标注服务更加稳定可靠！**
