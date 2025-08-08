# 🔧 Label Studio ML Backend 故障排除指南

## 问题：无法在Label Studio前端显示图片描述标注

### 已修复的问题

#### 1. JSON格式问题 ✅
**问题**: `text` 字段格式不正确
**修复**: 将 `"text": "内容"` 改为 `"text": ["内容"]`

```python
# 修复前
"value": {
    "text": "图片描述内容"
}

# 修复后  
"value": {
    "text": ["图片描述内容"]
}
```

#### 2. 字段名匹配问题 ✅
**问题**: `from_name` 和 `to_name` 字段名不匹配Label Studio配置
**修复**: 添加动态字段名获取功能

```python
def _get_field_names(self) -> tuple:
    """动态获取Label Studio配置中的字段名"""
    # 从Label Studio配置中自动获取正确的字段名
    return from_name, to_name
```

### 当前JSON格式

```json
{
  "model_version": "1.0.0-debug",
  "score": 0.95,
  "result": [
    {
      "from_name": "caption",      // 动态获取
      "to_name": "image",          // 动态获取
      "type": "textarea",
      "value": {
        "text": ["图片描述内容"]    // 数组格式
      }
    }
  ]
}
```

### 可能的问题和解决方案

#### 1. Label Studio项目配置问题

**检查项目配置**:
```xml
<View>
  <Image name="image" value="$captioning"/>
  <Header value="Describe the image:"/>
  <TextArea name="caption" toName="image" 
            placeholder="Enter description here..."
            rows="5" 
            maxSubmissions="1"
            editable="true"
            perRegion="false"
            required="false"/>
</View>
```

**关键配置**:
- `perRegion="false"` - 确保是全局文本区域，不是区域相关
- `toName="image"` - 确保指向正确的图片字段
- `name="caption"` - 确保字段名正确
- `value="$captioning"` - 图片数据字段名

#### 2. ML Backend连接问题

**检查连接**:
1. 确保ML Backend正在运行: `http://localhost:9090`
2. 在Label Studio项目设置中正确配置ML Backend URL
3. 启用"自动预标注"功能

#### 3. 图片数据问题

**检查任务数据**:
```json
{
  "data": {
    "captioning": "https://example.com/image.jpg"  // 或base64数据
  }
}
```

**支持的图片格式**:
- URL: `https://example.com/image.jpg`
- Base64: `data:image/jpeg;base64,/9j/4AAQSkZJRg...`
- 本地文件: `/path/to/image.jpg`

#### 4. API调用问题

**检查API配置**:
- 确保 `MODELSCOPE_API_KEY` 环境变量已设置
- 确保网络连接正常
- 检查API配额是否充足

### 调试步骤

#### 1. 检查ML Backend日志
```bash
# 启动时查看详细日志
label-studio-ml start ./ --debug

# 查看控制台输出
# 应该看到详细的处理过程
```

#### 2. 测试API连接
```bash
# 运行测试脚本
python debug_test.py
```

#### 3. 验证JSON格式
```bash
# 运行格式测试
python test_format.py
```

### 常见错误和解决方案

#### 错误1: "无法访问上传的图片文件"
**原因**: 文件路径配置问题
**解决**: 
1. 检查Label Studio媒体目录配置
2. 确保文件已正确上传
3. 使用Base64编码图片

#### 错误2: "API调用失败"
**原因**: 网络或配置问题
**解决**:
1. 检查API密钥是否正确
2. 验证网络连接
3. 检查API配额

#### 错误3: "字段名不匹配"
**原因**: Label Studio配置与代码不匹配
**解决**:
1. 检查项目配置中的字段名
2. 确保 `from_name` 和 `to_name` 正确
3. 使用动态字段名获取功能

### 最佳实践

1. **项目配置**:
   - 使用简单的配置开始测试
   - 确保字段名一致
   - 设置 `perRegion="false"`

2. **数据格式**:
   - 使用URL或Base64编码的图片
   - 确保图片格式支持
   - 检查图片大小限制

3. **调试**:
   - 启用详细日志
   - 逐步测试每个组件
   - 验证JSON格式正确

### 联系支持

如果问题仍然存在，请提供以下信息：
1. Label Studio项目配置
2. ML Backend日志输出
3. 任务数据示例
4. 错误信息详情 