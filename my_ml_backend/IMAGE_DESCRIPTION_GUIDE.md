# 🖼️ 图片描述文本标注ML Backend

## 📋 概述

本ML Backend使用魔塔社区的多模态模型 `Qwen/Qwen2.5-VL-72B-Instruct` 为图片生成详细的中文描述文本。

## 🎯 主要功能

- ✅ **多模态理解** - 支持图片+文本输入
- ✅ **中文描述** - 生成流畅的中文图片描述  
- ✅ **灵活输入** - 支持URL和Base64编码图片
- ✅ **自定义提示** - 支持用户自定义描述要求
- ✅ **详细分析** - 识别物体、场景、颜色、动作等

## 🔧 配置要求

### 环境变量
```bash
# 设置魔塔社区API密钥
export MODELSCOPE_API_KEY="your-api-key"

# PowerShell (Windows)
$env:MODELSCOPE_API_KEY="your-api-key"
```

### 依赖包
```bash
pip install openai>=1.0.0
```

## 🚀 启动方法

```bash
cd label-studio-ml-backend/my_ml_backend
label-studio-ml start ./
```

## 📝 支持的输入格式

### 1. 图片URL
```json
{
  "data": {
    "image": "https://example.com/sample.jpg",
    "text": "请描述这张图片"
  }
}
```

### 2. Base64编码图片
```json
{
  "data": {
    "img": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "prompt": "分析图片中的主要物体"
  }
}
```

### 3. 自定义描述要求
```json
{
  "data": {
    "image": "https://example.com/photo.png",
    "text": "请重点描述图片中的颜色搭配和光线效果"
  }
}
```

## 📊 输出格式

```json
{
  "model_version": "0.0.1",
  "score": 0.95,
  "result": [
    {
      "from_name": "description",
      "to_name": "image",
      "type": "textarea",
      "value": {
        "text": ["这是一张阳光明媚的户外风景照。图片中央是一棵高大的橡树..."]
      }
    }
  ]
}
```

## 🎨 Label Studio集成

### 1. 项目配置
在Label Studio中创建图片标注项目，使用以下标注界面配置：

```xml
<View>
  <Image name="image" value="$image"/>
  <TextArea name="description" toName="image" 
            placeholder="AI生成的图片描述将显示在这里"/>
</View>
```

### 2. ML Backend设置
- 在项目设置中添加ML Backend URL
- 启用自动预标注
- 选择合适的触发条件

### 3. 使用流程
1. 上传图片到Label Studio
2. ML Backend自动生成描述
3. 可手动编辑和完善描述
4. 保存标注结果

## 💡 描述特点

### 自动分析内容包括：
- **主要物体** - 识别图片中的人、物、动物等
- **场景环境** - 室内/户外、具体场所等
- **颜色光线** - 色彩搭配、明暗对比等  
- **动作状态** - 人物动作、物体状态等
- **细节特征** - 值得注意的细节信息

### 描述风格：
- 自然流畅的中文表达
- 结构化的信息组织
- 客观准确的内容描述
- 适合标注需求的详细程度

## 🔧 技术特性

| 特性 | 说明 |
|------|------|
| **模型** | Qwen/Qwen2.5-VL-72B-Instruct |
| **API** | 魔塔社区推理服务 |
| **输入** | 图片 + 可选文本提示 |
| **输出** | 中文描述文本 |
| **格式** | Label Studio Textarea |
| **编码** | 支持URL和Base64 |

## 🚨 注意事项

### 限制说明
- 图片大小建议不超过10MB
- 支持常见格式：JPG, PNG, GIF, WebP
- API调用需要网络连接
- 描述质量取决于图片清晰度

### 最佳实践
1. **图片质量** - 使用清晰、光线好的图片
2. **自定义提示** - 根据需要提供具体的描述要求
3. **手动校对** - AI描述可能需要人工调整
4. **批量处理** - 适合大量图片的自动化标注

## 📈 应用场景

- **数据集标注** - 为机器学习数据集添加描述
- **内容管理** - 为图片库生成元数据
- **无障碍服务** - 为视觉障碍用户提供图片描述
- **质量控制** - 自动生成初始描述，人工精调
- **批量处理** - 大规模图片内容分析

## 🎉 开始使用

1. **设置API密钥**
2. **启动ML Backend**
3. **在Label Studio中配置**
4. **上传图片测试**
5. **查看自动生成的描述**

现在您可以开始使用AI驱动的图片描述标注服务了！🚀