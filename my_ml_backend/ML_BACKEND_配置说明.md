# ML Backend 自动化标注平台配置说明

## 📖 概述

本项目支持自动配置 Label Studio 的 ML Backend，实现项目创建时自动连接机器学习后端，支持智能的文本命名实体识别自动标注。

## ⚙️ 配置参数

在 `auto_project_creator.py` 文件中，可以配置以下ML Backend参数：

### 基础配置

```python
# ML Backend 配置
ML_BACKEND_URL = "http://localhost:9090"          # ML Backend服务地址
ML_BACKEND_TITLE = "自动标注后端"                   # Backend显示名称
ML_BACKEND_DESCRIPTION = "用于文本命名实体识别的自动标注后端"  # Backend描述
ML_BACKEND_TIMEOUT = 30                           # 连接超时时间（秒）
REUSE_EXISTING_BACKEND = True                     # 是否重复使用已存在的Backend
```

### 参数说明

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `ML_BACKEND_URL` | str | "http://localhost:9090" | ML Backend服务的URL地址 |
| `ML_BACKEND_TITLE` | str | "自动标注后端" | 在Label Studio中显示的Backend名称 |
| `ML_BACKEND_DESCRIPTION` | str | "用于文本命名实体识别的自动标注后端" | Backend的描述信息 |
| `ML_BACKEND_TIMEOUT` | int | 30 | 连接和操作的超时时间（秒） |
| `REUSE_EXISTING_BACKEND` | bool | True | 是否重复使用已存在的相同URL的Backend |

## 🔧 配置策略

### 1. 重复使用现有Backend (推荐)

```python
REUSE_EXISTING_BACKEND = True
```

**优点：**
- 避免创建重复的ML Backend
- 节省系统资源
- 配置管理更简单

**适用场景：**
- 多次运行项目创建器
- 所有项目使用相同的ML模型
- 生产环境部署

### 2. 每次创建新Backend

```python
REUSE_EXISTING_BACKEND = False
```

**优点：**
- 每个项目独立的Backend配置
- 便于测试和调试
- 支持不同项目使用不同模型

**适用场景：**
- 开发和测试环境
- 需要为不同项目配置不同模型
- Backend配置经常变化

## 🔍 连接验证

项目创建器会自动验证以下连接：

### 1. Label Studio连接测试
```
🔍 测试服务连接...
✅ Label Studio连接成功
```

### 2. ML Backend健康检查
```
✅ ML Backend连接成功
```

**注意：** ML Backend连接失败不会阻止项目创建，但自动标注功能将不可用。

## 🚀 自动配置流程

每个项目创建时，系统会自动执行以下步骤：

### 1. 查找现有Backend
如果 `REUSE_EXISTING_BACKEND = True`：
```
🔍 找到已存在的ML Backend，ID: 1
```

### 2. 创建新Backend
如果需要创建新的Backend：
```
🔧 创建ML Backend: http://localhost:9090
✅ ML Backend创建成功，ID: 2
```

### 3. 连接到项目
```
🔗 连接ML Backend 1 到项目 5
✅ ML Backend连接到项目成功
🎉 项目 5 的ML Backend配置完成
```

## 🛠️ 高级配置

### 自定义ML Backend配置

如果需要更高级的配置，可以修改 `_create_ml_backend` 方法：

```python
def _create_ml_backend(self) -> Optional[int]:
    ml_backend_data = {
        "url": self.ml_backend_url,
        "title": self.ml_backend_title,
        "description": self.ml_backend_description,
        # 可以添加更多配置选项
        "model_version": "v1.0",
        "batch_size": 10,
        # ...
    }
```

### 连接超时配置

根据网络环境调整超时时间：

```python
# 快速网络环境
ML_BACKEND_TIMEOUT = 10  

# 一般网络环境  
ML_BACKEND_TIMEOUT = 30

# 慢速网络环境
ML_BACKEND_TIMEOUT = 60
```

## 🔧 故障排除

### 1. ML Backend连接失败

**症状：**
```
⚠️ ML Backend连接测试失败: Connection refused
```

**解决方案：**
1. 确认ML Backend服务正在运行：
   ```bash
   curl http://localhost:9090/health
   ```
2. 检查端口是否正确
3. 确认防火墙设置

### 2. Backend创建失败

**症状：**
```
❌ ML Backend创建失败: 400 - Bad Request
```

**解决方案：**
1. 检查Label Studio API权限
2. 验证Backend URL格式
3. 查看详细错误日志

### 3. 连接到项目失败

**症状：**
```
❌ ML Backend连接失败: 404 - Not Found
```

**解决方案：**
1. 确认项目ID正确
2. 检查Backend ID是否有效
3. 验证API令牌权限

## 📋 最佳实践

### 1. 生产环境配置
```python
ML_BACKEND_URL = "http://ml-backend.company.com:9090"
ML_BACKEND_TITLE = "生产环境NER标注服务"
ML_BACKEND_DESCRIPTION = "企业级命名实体识别自动标注服务"
ML_BACKEND_TIMEOUT = 60
REUSE_EXISTING_BACKEND = True
```

### 2. 开发环境配置
```python
ML_BACKEND_URL = "http://localhost:9090"
ML_BACKEND_TITLE = "开发环境测试Backend"
ML_BACKEND_DESCRIPTION = "用于开发测试的ML Backend"
ML_BACKEND_TIMEOUT = 30
REUSE_EXISTING_BACKEND = False
```

### 3. 多环境配置

可以通过环境变量动态配置：

```python
import os

ML_BACKEND_URL = os.getenv("ML_BACKEND_URL", "http://localhost:9090")
ML_BACKEND_TITLE = os.getenv("ML_BACKEND_TITLE", "自动标注后端")
REUSE_EXISTING_BACKEND = os.getenv("REUSE_BACKEND", "true").lower() == "true"
```

## 🔗 相关文档

- [Label Studio ML Backend 官方文档](https://labelstud.io/guide/ml.html)
- [项目自动创建器使用说明](./使用说明_项目自动创建.md)
- [自动标注器使用说明](./README_AUTO_LABELER.md)

---

💡 **提示：** 合理配置ML Backend参数可以显著提高项目创建效率和自动标注准确性。建议根据实际使用场景选择合适的配置策略。
