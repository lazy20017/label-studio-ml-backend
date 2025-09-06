# Label Studio 标注结果自动导出器使用指南

## 📋 程序简介

`auto_annotation_exporter.py` 是一个功能强大的 Label Studio 项目标注结果自动导出工具，支持批量导出项目的标注数据为结构化的 JSON 格式。

### 🌟 主要特性

- **🔄 批量导出**：支持单个项目、多个项目或所有项目的标注结果导出
- **📊 结构化输出**：以标准化 JSON 格式导出标注数据
- **💾 灵活保存**：支持单独文件或合并文件保存
- **📝 详细统计**：显示导出进度和完整统计信息
- **⚙️ 灵活配置**：可自定义导出选项和参数
- **🎯 完整数据**：包含任务、标注、预测、元数据等完整信息

## 🚀 快速开始

### 1. 配置参数

在程序开头修改配置参数：

```python
# Label Studio 配置
LABEL_STUDIO_URL = "http://localhost:8080"          # Label Studio服务地址
LABEL_STUDIO_API_TOKEN = "your_api_token_here"      # 您的API令牌

# 导出配置
DEFAULT_OUTPUT_DIR = "exported_annotations"         # 默认导出目录
INCLUDE_TASK_DATA = True                            # 是否包含原始任务数据
INCLUDE_PREDICTIONS = True                          # 是否包含预测结果
INCLUDE_METADATA = True                             # 是否包含元数据
PRETTY_JSON = True                                  # 是否美化JSON输出
```

### 2. 运行程序

```bash
cd label-studio-ml-backend/my_ml_backend
python auto_annotation_exporter.py
```

### 3. 交互式操作

程序启动后会显示交互式菜单：

```
📋 选择导出模式:
1. 导出单个项目
2. 导出多个项目
3. 导出所有项目
4. 查看项目列表
5. 退出
```

## 📖 详细使用说明

### 导出模式说明

#### 1. 导出单个项目
- 输入项目ID，导出指定项目的所有标注结果
- 生成文件：`project_{项目ID}_annotations.json`

#### 2. 导出多个项目
- 输入多个项目ID（用逗号分隔），批量导出
- 可选择是否合并到一个文件
- 生成文件：每个项目单独文件 + 可选合并文件

#### 3. 导出所有项目
- 自动获取所有项目并批量导出
- 默认合并到一个文件
- 生成文件：`all_projects_annotations.json`

#### 4. 查看项目列表
- 显示所有项目的ID、名称、任务数、创建时间
- 方便选择要导出的项目

### 导出数据结构

导出的 JSON 数据包含以下结构：

```json
{
  "export_info": {
    "exported_at": "2025-01-28T15:30:00",
    "label_studio_url": "http://localhost:8080",
    "exporter_version": "1.0.0"
  },
  "project_info": {
    "project_id": 1,
    "title": "项目名称",
    "description": "项目描述",
    "created_at": "2025-01-28T10:00:00",
    "updated_at": "2025-01-28T15:00:00",
    "label_config": "<View>...</View>"
  },
  "statistics": {
    "total_tasks": 100,
    "annotated_tasks": 80,
    "total_annotations": 120,
    "completion_rate": 80.0
  },
  "tasks": [
    {
      "task_id": 1,
      "created_at": "2025-01-28T10:00:00",
      "updated_at": "2025-01-28T15:00:00",
      "data": {
        "text": "原始文本内容"
      },
      "annotations": [
        {
          "annotation_id": 1,
          "created_at": "2025-01-28T14:00:00",
          "updated_at": "2025-01-28T14:30:00",
          "created_by": 1,
          "lead_time": 180.5,
          "result": [
            {
              "value": {
                "start": 0,
                "end": 6,
                "text": "实体文本",
                "labels": ["人名"]
              },
              "from_name": "label",
              "to_name": "text",
              "type": "labels"
            }
          ],
          "metadata": {
            "was_cancelled": false,
            "ground_truth": false,
            "unique_id": "unique_annotation_id",
            "import_id": null
          }
        }
      ],
      "predictions": [
        {
          "prediction_id": 1,
          "created_at": "2025-01-28T13:00:00",
          "model_version": "1.0.0",
          "score": 0.95,
          "result": [
            {
              "value": {
                "start": 0,
                "end": 6,
                "text": "实体文本",
                "labels": ["人名"]
              },
              "from_name": "label",
              "to_name": "text",
              "type": "labels",
              "score": 0.95
            }
          ]
        }
      ]
    }
  ]
}
```

## ⚙️ 配置选项详解

### 基础配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `LABEL_STUDIO_URL` | Label Studio 服务地址 | `http://localhost:8080` |
| `LABEL_STUDIO_API_TOKEN` | API 访问令牌 | 需要配置 |
| `DEFAULT_OUTPUT_DIR` | 默认导出目录 | `exported_annotations` |
| `REQUEST_TIMEOUT` | 单个请求超时时间（秒） | `60` |
| `DELAY_BETWEEN_REQUESTS` | 请求间延迟时间（秒） | `0.5` |

### 导出选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `INCLUDE_TASK_DATA` | 是否包含原始任务数据 | `True` |
| `INCLUDE_PREDICTIONS` | 是否包含预测结果 | `True` |
| `INCLUDE_METADATA` | 是否包含元数据 | `True` |
| `PRETTY_JSON` | 是否美化 JSON 输出 | `True` |

### 日志配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `LOG_LEVEL` | 日志级别 | `logging.INFO` |
| `SAVE_DETAILED_LOG` | 是否保存详细日志到文件 | `True` |

## 📁 输出文件说明

### 文件命名规则

- **单个项目**：`project_{项目ID}_annotations.json`
- **多个项目合并**：`multiple_projects_annotations.json`
- **所有项目合并**：`all_projects_annotations.json`
- **日志文件**：`auto_annotation_exporter_{时间戳}.log`

### 输出目录结构

```
exported_annotations/
├── project_1_annotations.json      # 项目1的标注结果
├── project_2_annotations.json      # 项目2的标注结果
├── all_projects_annotations.json   # 所有项目合并结果
└── auto_annotation_exporter_20250128_153000.log  # 导出日志
```

## 🛠️ 编程接口使用

除了交互式使用，您也可以在代码中直接使用导出器：

```python
from auto_annotation_exporter import AutoAnnotationExporter

# 创建导出器实例
exporter = AutoAnnotationExporter(
    label_studio_url="http://localhost:8080",
    api_token="your_api_token",
    output_dir="my_exports"
)

# 测试连接
if exporter.test_connection():
    # 导出单个项目
    result = exporter.export_project(project_id=1, output_file="project_1.json")
    
    # 导出多个项目
    results = exporter.export_multiple_projects([1, 2, 3], separate_files=True)
    
    # 导出所有项目
    all_results = exporter.export_all_projects(combined_file="all_projects.json")
    
    # 显示统计信息
    exporter.print_statistics()
```

## 📊 统计信息

程序会显示详细的导出统计信息：

```
📊 标注结果导出统计信息
============================================================
📋 总项目数: 5
✅ 导出成功: 4
❌ 导出失败: 1
📝 总任务数: 250
🏷️ 总标注数: 180
📈 导出成功率: 80.0%
📁 输出目录: /path/to/exported_annotations
============================================================
```

## 🔧 常见问题

### Q1: 连接失败怎么办？
**A**: 检查以下配置：
- Label Studio 服务是否正常运行
- URL 地址是否正确
- API Token 是否有效
- 网络连接是否正常

### Q2: 导出文件很大怎么办？
**A**: 可以调整导出选项：
- 设置 `INCLUDE_TASK_DATA = False` 减少原始数据
- 设置 `INCLUDE_PREDICTIONS = False` 排除预测结果
- 设置 `PRETTY_JSON = False` 压缩 JSON 格式

### Q3: 如何导出特定时间范围的标注？
**A**: 当前版本导出所有标注，可以从导出的 JSON 中根据 `created_at` 字段进行过滤。

### Q4: 如何获取 API Token？
**A**: 
1. 登录 Label Studio
2. 进入 Account Settings
3. 在 Access Token 部分复制令牌

### Q5: 支持哪些项目类型？
**A**: 支持所有 Label Studio 项目类型，包括：
- 文本分类
- 命名实体识别
- 图像标注
- 音频标注
- 视频标注等

## 🎯 使用示例

### 示例1：导出单个NER项目

```bash
# 运行程序
python auto_annotation_exporter.py

# 选择操作
请选择操作 (1-5): 1

# 输入项目ID
请输入项目ID: 5

# 结果
✅ 项目 5 导出成功
💾 项目 5 标注结果已保存到: exported_annotations/project_5_annotations.json
```

### 示例2：批量导出多个项目

```bash
# 选择操作
请选择操作 (1-5): 2

# 输入项目ID列表
请输入项目ID，用逗号分隔 (例如: 1,2,3)
项目ID列表: 1,3,5,7

# 是否合并文件
是否将所有项目合并到一个文件? (y/N): y

# 结果
✅ 成功导出 4 个项目，失败 0 个项目
💾 所有项目的合并结果已保存到: exported_annotations/multiple_projects_annotations.json
```

### 示例3：导出所有项目

```bash
# 选择操作
请选择操作 (1-5): 3

# 是否合并文件
是否将所有项目合并到一个文件? (Y/n): Y

# 结果
📋 找到 10 个项目
✅ 成功导出 10 个项目，失败 0 个项目
💾 所有项目的合并结果已保存到: exported_annotations/all_projects_annotations.json
```

## 🔄 版本历史

### v1.0.0 (2025-01-28)
- ✨ 初始版本发布
- 🎯 支持单个/多个/所有项目导出
- 📊 完整的 JSON 数据结构
- 📝 详细的统计信息
- ⚙️ 灵活的配置选项

## 📞 技术支持

如有问题或建议，请查看：
- 程序日志文件获取详细错误信息
- Label Studio 官方文档
- 本项目的其他使用指南

---

🎉 感谢使用 Label Studio 标注结果自动导出器！
