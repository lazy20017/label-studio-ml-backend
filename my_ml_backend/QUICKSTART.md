# 🚀 快速启动指南 - 魔塔社区API文本标注

在5分钟内快速配置和运行Label Studio ML Backend。

## 📋 1. 前置准备

### 必需条件
- ✅ Python 3.7+
- ✅ 魔塔社区账号
- ✅ 网络连接

### 获取API Key
1. 访问 [魔塔社区](https://www.modelscope.cn/)
2. 注册/登录账号
3. 进入个人中心
4. 复制API Access Token

## ⚙️ 2. 环境配置

### Windows (PowerShell)
```powershell
# 设置API Key
$env:MODELSCOPE_API_KEY='your_api_key_here'

# 验证设置
echo $env:MODELSCOPE_API_KEY
```

### Linux/Mac
```bash
# 设置API Key
export MODELSCOPE_API_KEY=your_api_key_here

# 验证设置
echo $MODELSCOPE_API_KEY

# 持久化设置（可选）
echo "export MODELSCOPE_API_KEY=your_api_key_here" >> ~/.bashrc
source ~/.bashrc
```

## 🔧 3. 安装和启动

### 安装依赖
```bash
cd label-studio-ml-backend/my_ml_backend
pip install -r requirements.txt
```

注意：新版本已添加`openai`依赖，用于更简洁的API调用。

### 环境检查
```bash
# 检查环境配置
python check_modelscope_env.py
```

应该看到：
```
✅ MODELSCOPE_API_KEY: ***12345678 (已设置)
✅ OpenAI客户端初始化成功
✅ API连接成功
✅ 模型响应正常
```

### OpenAI客户端连接测试
```bash
# 测试OpenAI客户端实现
python test_openai_client.py
```

这将验证：
- ✅ OpenAI客户端初始化
- ✅ 基本聊天功能
- ✅ 流式响应支持
- ✅ Token使用统计

### 启动ML Backend
```bash
label-studio-ml start ./
```

成功启动会显示：
```
✅ 魔塔社区API连接成功
✅ 模型 Qwen/Qwen3-Coder-480B-A35B-Instruct 可用
ML Backend started at http://localhost:9090
```

## 🧪 4. 功能测试

### 快速测试
```bash
# 运行预设测试用例
python test_modelscope_text.py
```

### 自定义测试
```bash
# 启动后，可以测试各种文本标注任务：
# - 代码分析
# - 文档分类  
# - 技术问答
# - 错误调试
```

## 🏷️ 5. 在Label Studio中配置

### 创建项目
1. 打开Label Studio: http://localhost:8080
2. 创建新项目
3. 导入文本数据

### 设置标签配置
选择适合的任务类型：

**文本分类**:
```xml
<Text name="text" value="$text"/>
<Choices name="category" toName="text">
  <Choice value="技术文档"/>
  <Choice value="业务需求"/>
  <Choice value="错误报告"/>
</Choices>
```

**文本分析**:
```xml
<Text name="text" value="$text"/>
<TextArea name="analysis" toName="text" placeholder="分析文本内容..."/>
```

### 连接ML Backend
1. 进入项目设置
2. 点击 "Machine Learning"
3. 添加模型: `http://localhost:9090`
4. 点击 "Validate and Save"

## ✅ 6. 验证运行

### 检查连接状态
在Label Studio ML页面应该显示：
- ✅ 连接状态：正常
- ✅ 模型版本：0.0.1
- ✅ 支持的任务：文本标注

### 测试预测
1. 在Label Studio中打开一个任务
2. 点击 "Get Predictions" 按钮
3. 应该看到AI生成的标注结果

## 🎯 常用任务示例

### 代码注释生成
```python
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)
```

### 技术文档分类
```
这是一个关于机器学习的技术文档，主要介绍了深度学习算法的应用。
```

### 错误调试
```
Traceback (most recent call last):
  File "main.py", line 15, in <module>
    result = divide(10, 0)
ZeroDivisionError: division by zero
```

## 🚨 故障排除

### 环境问题
```bash
# 重新检查环境
python check_modelscope_env.py

# 查看详细日志
label-studio-ml start ./ --debug
```

### 常见错误
- **API Key错误**: 检查是否正确设置环境变量
- **网络问题**: 验证能否访问魔塔社区
- **权限错误**: 确认账号有模型访问权限
- **配额不足**: 检查API调用剩余次数

### 获取帮助
- 查看完整文档: [README.md](README.md)
- 运行诊断工具: `python test_modelscope_text.py`
- 检查控制台日志获取详细错误信息

---

🎉 **恭喜！** 现在你可以在Label Studio中使用强大的Qwen3-Coder模型进行文本标注了！

💡 **下一步**: 尝试不同的标签配置和任务类型，探索AI辅助标注的强大功能。