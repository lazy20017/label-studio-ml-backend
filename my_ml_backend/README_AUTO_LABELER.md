# Label Studio 自动串行标注器使用说明

## 📖 简介

`auto_serial_labeler.py` 是一个专门为Label Studio设计的自动标注工具，能够：

- 🔄 **串行处理**：逐个提交任务到ML Backend进行预测，确保前一个完成后再处理下一个
- 📊 **实时进度**：显示详细的处理进度和统计信息
- 💾 **自动保存**：预测结果自动保存为标注到Label Studio
- 🔁 **智能重试**：失败任务自动重试，提高成功率
- 📝 **详细日志**：记录所有处理过程，便于调试和监控

## 🚀 快速开始

### 1. 配置参数

打开 `auto_serial_labeler.py` 文件，修改顶部的配置区域：

```python
# ================================
# 用户配置区域 - 请根据实际情况修改
# ================================

# Label Studio 配置
LABEL_STUDIO_URL = "http://localhost:8080"          # 您的Label Studio地址
LABEL_STUDIO_API_TOKEN = "your_api_token_here"     # 在Account Settings中获取
PROJECT_ID = 1                                      # 项目ID，在项目URL中找到

# ML Backend 配置  
ML_BACKEND_URL = "http://localhost:9090"            # ML Backend地址

# 处理配置
MAX_TASKS = None                                    # 最大任务数，None=处理所有
DELAY_BETWEEN_TASKS = 1.0                          # 任务间延迟（秒）
MAX_RETRIES = 3                                    # 失败重试次数
```

### 2. 获取API令牌

1. 登录Label Studio
2. 点击右上角用户头像 → **Account Settings**
3. 在 **Access Token** 部分复制令牌
4. 将令牌粘贴到 `LABEL_STUDIO_API_TOKEN` 变量中

### 3. 确认项目ID

在Label Studio中打开您的项目，URL类似：`http://localhost:8080/projects/1/data`
其中数字 `1` 就是项目ID。

### 4. 运行程序

```bash
cd label-studio-ml-backend/my_ml_backend
python auto_serial_labeler.py
```

## ⚙️ 配置说明

### 基本配置

| 参数 | 说明 | 示例 |
|------|------|------|
| `LABEL_STUDIO_URL` | Label Studio服务地址 | `"http://localhost:8080"` |
| `LABEL_STUDIO_API_TOKEN` | API访问令牌 | `"a1b2c3d4e5f6..."` |
| `PROJECT_ID` | 项目ID | `1` |
| `ML_BACKEND_URL` | ML Backend服务地址 | `"http://localhost:9090"` |

### 处理配置

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `MAX_TASKS` | 最大处理任务数 | `None`（处理所有）或 `50` |
| `DELAY_BETWEEN_TASKS` | 任务间延迟时间（秒） | `1.0` |
| `MAX_RETRIES` | 失败任务重试次数 | `3` |
| `REQUEST_TIMEOUT` | 请求超时时间（秒） | `300` |

### 日志配置

| 参数 | 说明 | 选项 |
|------|------|------|
| `LOG_LEVEL` | 日志级别 | `logging.INFO` / `logging.DEBUG` |
| `SAVE_DETAILED_LOG` | 是否保存日志文件 | `True` / `False` |

## 📊 运行界面

程序运行时会显示类似以下的输出：

```
🤖 Label Studio 自动串行标注器
============================================================
📝 程序说明:
   • 自动获取未标注任务
   • 串行提交ML Backend进行预测
   • 自动保存标注结果到Label Studio
   • 支持失败重试和详细日志
============================================================
⚙️ 配置检查:
   Label Studio: http://localhost:8080
   ML Backend: http://localhost:9090
   项目ID: 1
   最大任务数: 无限制
   任务间延迟: 1.0秒
   最大重试: 3次
============================================================

📋 确认配置无误，按回车开始处理，或输入 'q' 退出: 

✅ 自动串行标注器初始化完成
🔍 测试服务连接...
✅ Label Studio连接成功
   项目名称: 我的NER项目
✅ ML Backend连接成功

🔍 获取未标注任务...
📊 项目总任务数: 150
🎯 未标注任务数: 25
📋 准备处理 25 个任务

========================================
🔄 处理任务 1/25 (ID: 101)
========================================
   📝 内容预览: 今天北京市发生了一起火灾事故，消防部门迅速响应...
✅ 任务 101 处理成功 (识别到 8 个实体)
📊 任务 1 完成: ✅ 成功 (耗时: 3.45秒)
📈 总进度: 1/25 (4.0%) | 成功率: 100.0%
⏱️ 等待 1.0秒后处理下一个任务...
```

## 📁 输出文件

程序会生成以下文件：

### 日志文件
- 位置：`logs/auto_labeler_YYYYMMDD_HHMMSS.log`
- 内容：详细的处理日志，包括每个任务的处理过程和错误信息

### 临时文件
程序运行时不会产生其他临时文件，所有结果直接保存到Label Studio。

## 🔧 高级用法

### 处理特定数量的任务

```python
MAX_TASKS = 50  # 只处理前50个未标注任务
```

### 调整性能参数

```python
DELAY_BETWEEN_TASKS = 0.5    # 减少延迟以提高速度
MAX_RETRIES = 5              # 增加重试次数以提高成功率
REQUEST_TIMEOUT = 600        # 增加超时时间处理复杂任务
```

### 启用调试模式

```python
LOG_LEVEL = logging.DEBUG    # 显示更详细的调试信息
```

## ❗ 注意事项

### 必要条件
1. ✅ Label Studio 正在运行
2. ✅ ML Backend 正在运行且已连接到Label Studio
3. ✅ 已设置正确的API令牌
4. ✅ 项目中有未标注的任务

### 安全性
- 🔒 API令牌具有访问您Label Studio数据的权限，请妥善保管
- 🔒 不要在公共代码仓库中提交包含真实令牌的代码

### 性能建议
- 📈 建议设置合理的 `DELAY_BETWEEN_TASKS` 避免对服务器造成压力
- 📈 对于大量任务，可以分批处理（设置 `MAX_TASKS`）
- 📈 监控ML Backend的内存和CPU使用情况

## 🐛 故障排除

### 常见错误

#### 1. API令牌错误
```
❌ Label Studio连接失败: 401 Client Error: Unauthorized
```
**解决方案**：检查API令牌是否正确，是否已在Label Studio中生成。

#### 2. 项目ID错误
```
❌ Label Studio连接失败: 404 Client Error: Not Found
```
**解决方案**：检查项目ID是否正确，确认项目存在且有访问权限。

#### 3. ML Backend连接失败
```
❌ 任务 123 预测请求失败: Connection refused
```
**解决方案**：
- 检查ML Backend是否正在运行
- 确认ML Backend URL是否正确
- 检查网络连接

#### 4. 没有未标注任务
```
🎉 没有需要标注的任务
```
**说明**：所有任务都已标注完成，这是正常情况。

### 调试技巧

1. **启用详细日志**：
   ```python
   LOG_LEVEL = logging.DEBUG
   ```

2. **减少任务数量测试**：
   ```python
   MAX_TASKS = 1  # 先处理1个任务测试
   ```

3. **检查日志文件**：
   查看 `logs/` 目录下的详细日志文件。

## 📧 技术支持

如遇到问题，请提供以下信息：
- 错误信息截图
- 配置参数设置
- 日志文件内容
- Label Studio 和 ML Backend 版本

## 📄 许可证

此工具遵循 MIT 许可证，可自由使用和修改。
