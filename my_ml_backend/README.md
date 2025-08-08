# Label Studio ML Backend - 魔塔社区 Qwen3-Coder-480B-A35B-Instruct

这是一个集成了魔塔社区Qwen3-Coder-480B-A35B-Instruct模型的Label Studio ML Backend，专注于文本标注任务。

## 🚀 功能特点

- ✅ 支持纯文本标注任务
- ✅ 代码分析和注释生成
- ✅ 技术文档理解和分类
- ✅ 错误调试和问题解答
- ✅ 自动适配Label Studio标签配置
- ✅ 支持分类和文本生成任务
- ✅ 完善的错误处理和日志记录

## 📋 前置要求

1. **魔塔社区API Key**: 需要有效的API访问令牌
2. **网络连接**: 确保能访问魔塔社区API服务
3. **Python环境**: Python 3.7+

## ⚙️ 配置

### 必需环境变量

```bash
# 魔塔社区API配置
export MODELSCOPE_API_KEY=your_api_key_here    # 必需: 魔塔社区API密钥

# 可选配置
export MODELSCOPE_API_URL=https://api-inference.modelscope.cn/v1  # 可选: 自定义API地址（使用OpenAI兼容格式）

# Label Studio配置（如需下载内部资源）
export LABEL_STUDIO_URL=http://localhost:8080
export LABEL_STUDIO_API_KEY=your_label_studio_api_key
```

### 技术实现

本ML Backend使用**OpenAI客户端库**连接魔塔社区API，具有以下优势：
- ✅ **标准接口**: 使用OpenAI兼容的API格式
- ✅ **简化代码**: 无需手动处理HTTP请求和响应解析
- ✅ **流式支持**: 支持流式和非流式响应
- ✅ **错误处理**: 自动处理连接错误和重试机制
- ✅ **类型安全**: 完整的类型提示和IDE支持

### 获取API Key

1. **访问魔塔社区**: https://www.modelscope.cn/
2. **注册/登录账号**: 创建或登录你的账号
3. **获取API Token**: 进入个人中心，获取API访问令牌
4. **设置环境变量**: 将Token设置为环境变量

### 启动后端

1. **设置API Key**:
   ```bash
   export MODELSCOPE_API_KEY=your_api_key_here
   ```

2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

3. **启动ML Backend**:
   ```bash
   label-studio-ml start ./my_ml_backend
   ```

4. **在Label Studio中连接**:
   - 进入项目设置 → Machine Learning
   - 添加模型: `http://localhost:9090`

## 🎯 支持的任务类型

### 1. 文本分类
```xml
<Text name="text" value="$text"/>
<Choices name="category" toName="text">
  <Choice value="技术文档"/>
  <Choice value="业务需求"/>
  <Choice value="错误报告"/>
</Choices>
```

### 2. 代码注释生成
```xml
<Text name="code" value="$code"/>
<TextArea name="comment" toName="code" placeholder="为代码添加注释..."/>
```

### 3. 文本分析和标注
```xml
<Text name="text" value="$text"/>
<TextArea name="analysis" toName="text" placeholder="分析文本内容..."/>
```

### 4. 技术问答
```xml
<Text name="question" value="$question"/>
<TextArea name="answer" toName="question" placeholder="提供技术解答..."/>
```

### 5. 错误调试分析
```xml
<Text name="error_log" value="$error_log"/>
<TextArea name="solution" toName="error_log" placeholder="错误分析和解决方案..."/>
```

## 🔧 自定义配置

### 修改模型参数

在 `model.py` 的 `_call_modelscope_api` 方法中：

```python
"parameters": {
    "max_tokens": 2000,    # 最大输出长度
    "temperature": 0.1,    # 控制输出随机性
    "top_p": 0.9          # 核心采样参数
}
```

### 更换模型

修改 `setup` 方法中的模型名称：

```python
self.model_name = "Qwen/Qwen3-Coder-480B-A35B-Instruct"  # 改为其他魔塔社区模型
```

### 自定义API地址

如果需要使用不同的API端点：

```bash
export MODELSCOPE_API_URL=https://your-custom-api-endpoint.com/v1/chat/completions
```

## 📊 性能建议

- **超时设置**: API调用已设置60秒超时，适合大多数文本处理任务
- **并发处理**: 单任务顺序处理，避免API调用冲突  
- **文本长度**: 建议单次处理文本不超过4000字符以提高响应速度
- **API配额**: 注意魔塔社区API的调用频率限制和配额管理

## 🐛 故障排除

### 🛠️ 诊断工具

在遇到问题时，请使用以下诊断工具：

1. **环境配置全面检查**:
   ```bash
   python check_modelscope_env.py
   ```

2. **OpenAI客户端连接测试**:
   ```bash
   python test_openai_client.py
   ```

3. **魔塔社区API功能测试**:
   ```bash
   python test_modelscope_text.py
   ```

4. **ML Backend健康检查**:
   ```bash
   python test_ml_backend.py
   ```

### 🐛 完整调试模式

**当前版本已启用超详细调试模式**，所有方法都会输出详细信息：

#### 调试输出包含：

**SETUP方法**:
- 环境变量读取
- 魔塔社区API配置过程
- 连接测试结果
- 项目上下文信息

**PREDICT方法**:
- 接收的完整任务数据
- 每个字段的类型和值
- 文本处理过程
- 魔塔社区API调用详情
- Token使用统计
- 最终预测结果

**FIT方法**:
- 训练事件信息
- 完整数据负载
- 缓存操作记录

#### 快速测试工具

```bash
# 魔塔社区API文本标注测试
python test_modelscope_text.py

# 标准ML Backend测试
python test_ml_backend.py http://localhost:9090
```

### 常见问题

1. **API Key未设置**
   ```
   ❌ API Key未设置
   ```
   **解决方案**:
   ```bash
   # 设置魔塔社区API Key
   export MODELSCOPE_API_KEY=your_api_key_here
   
   # 验证设置
   echo $MODELSCOPE_API_KEY
   ```

2. **API认证失败**
   ```
   ❌ API认证失败，请检查API Key
   ```
   **解决方案**:
   - 验证API Key是否正确
   - 检查API Key是否过期
   - 确认账号有权限访问该模型

3. **网络连接失败**
   ```
   ❌ 网络连接失败
   ```
   **解决方案**:
   - 检查网络连接是否正常
   - 验证防火墙设置
   - 尝试ping魔塔社区域名

4. **模型访问权限错误**
   ```
   ❌ 无权限访问此模型
   ```
   **解决方案**:
   - 确认账号已开通该模型的访问权限
   - 检查API调用配额是否充足
   - 联系魔塔社区客服开通权限

5. **请求超时**
   ```
   ❌ 请求超时 - 网络较慢，请稍后重试
   ```
   **解决方案**:
   - 检查网络稳定性
   - 减少文本长度重试
   - 增加超时时间设置

6. **API响应格式异常**
   ```
   ⚠️ 响应格式异常
   ```
   **解决方案**:
   - 检查API版本是否匹配
   - 验证请求参数格式
   - 查看详细错误日志

7. **文本处理失败**
   ```
   ❌ 未找到文本内容
   ```
   **解决方案**:
   ```bash
   # 运行文本标注测试
   python test_modelscope_text.py
   
   # 检查任务数据格式
   # 确保字段名为: text, content, question 等
   ```

8. **Token配额超限**
   ```
   ❌ API调用配额已用完
   ```
   **解决方案**:
   - 检查账号配额使用情况
   - 升级账号套餐
   - 优化API调用频率

### 调试模式

查看ML Backend控制台输出，获取详细的调试信息：

```bash
# 启动时会显示详细的配置和连接信息
label-studio-ml start ./

# 查看API调用详情
tail -f logs/ml_backend.log
```

## 📝 API响应格式

模型返回的预测格式符合Label Studio标准：

```json
{
  "model_version": "0.0.1",
  "score": 0.95,
  "result": [
    {
      "from_name": "analysis", 
      "to_name": "text",
      "type": "textarea",
      "value": {
        "text": ["这是Qwen3-Coder模型的分析结果"]
      }
    }
  ]
}
```

## 🎯 最佳实践

1. **文本预处理**: 清理输入文本，去除无关字符
2. **提示词优化**: 针对具体任务调整提示词
3. **结果后处理**: 对AI输出进行格式化和验证
4. **配额管理**: 监控API调用次数和费用
5. **错误重试**: 实现合理的重试机制

---

🎉 现在你可以在Label Studio中使用强大的Qwen3-Coder-480B-A35B-Instruct模型进行文本标注任务了！