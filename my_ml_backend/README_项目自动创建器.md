# Label Studio 项目自动化管理工具使用手册 📚

## 🌟 概述

本工具集提供了完整的 Label Studio 项目管理解决方案，包括项目的**创建**、**查询**、**删除**和**自动标注**功能。适用于需要批量处理文本文档并进行命名实体识别（NER）标注的场景。

## 📦 工具组件

### 核心模块
- `run_project_creator.py` - 快速启动脚本，调用- `auto_project_creator.py` - 项目自动创建器

- `query_projects.py` - 项目查询和删除项目使用，修改程序里面序号483行位置

- `auto_serial_labeler.py` - 自动标注器，项目批量标注，但是受限于大模型调用次数，1天2000次，1个模型500次

### 配置文件
- `文本命名实体提取标签.md` - 标注配置模板
- `entity_config.py` - 实体配置
- `entity_config_flood_optimized.py` - 防洪优化配置

## 🚀 快速开始

### 1. 环境准备

#### 启动服务
```bash
# 启动 Label Studio (端口 8080)
label-studio start

# 启动 ML Backend (端口 9090)
cd label-studio-ml-backend/my_ml_backend
label-studio-ml start ./
```

#### 配置 API 令牌
在相关 Python 文件中修改配置：
```python
LABEL_STUDIO_URL = "http://localhost:8080"
LABEL_STUDIO_API_TOKEN = "your_api_token_here"  # 替换为您的令牌
```

**获取 API 令牌步骤：**
1. 登录 Label Studio Web 界面
2. 点击右上角用户头像 → Account Settings
3. 在 Access Token 部分复制令牌

### 2. 文件结构准备

确保以下目录结构：
```
label-studio-ml-backend/my_ml_backend/
├── inputfile/                    # 输入文件目录
│   ├── 事故信息/                  # 事故相关文档
│   ├── 应急预案/                  # 应急预案文档
│   ├── 法律法规/                  # 法律法规文档
│   └── 防洪规范/                  # 防洪规范文档
├── 文本命名实体提取标签.md         # 标注配置文件
└── [工具脚本文件]
```

## 🛠️ 功能详解

## 一、项目自动创建 🏗️

### 功能特点
- 🔍 **智能扫描**：递归扫描 `inputfile` 目录下所有 `.txt` 文件
- 🏗️ **批量创建**：根据文件路径自动生成项目名称并创建项目
- 🏷️ **配置应用**：自动应用 NER 标注配置
- 🔗 **后端连接**：自动配置 ML Backend 进行预标注
- 📥 **文档导入**：自动导入对应文档内容
- 🧹 **内容优化**：自动清理空行和格式化文本

### 使用方法

#### 方法一：使用快速启动脚本（推荐）
```bash
cd label-studio-ml-backend/my_ml_backend
python run_project_creator.py
```

#### 方法二：直接运行创建器
```bash
python auto_project_creator.py
```

### 项目命名规则
项目名称基于文件的相对路径生成：

| 文件路径 | 生成的项目名称 |
|---------|---------------|
| `应急预案/01-国家自然灾害救助应急预案.txt` | `应急预案_01-国家自然灾害救助应急预案` |
| `法律法规/水污染防治法.txt` | `法律法规_水污染防治法` |
| `事故信息/flood_report.txt` | `事故信息_flood_report` |

### 创建流程
1. **环境检查** - 验证 Label Studio 和 ML Backend 连接
2. **文件扫描** - 递归扫描指定目录下的文本文件
3. **项目创建** - 为每个文件创建对应的 Label Studio 项目
4. **配置应用** - 应用 NER 标注配置
5. **后端连接** - 连接 ML Backend 实现自动预标注
6. **文档导入** - 导入文本内容作为标注任务
7. **结果报告** - 显示创建统计和项目列表

### 配置选项
```python
# 文件和路径配置
INPUT_FILE_DIR = "inputfile"  # 输入文件目录
LABEL_CONFIG_FILE = "文本命名实体提取标签.md"  # 标签配置文件

# 项目配置
PROJECT_DESCRIPTION_TEMPLATE = "基于{filename}的文本命名实体提取项目，自动创建于{date}"
DELAY_BETWEEN_REQUESTS = 0.5  # 请求间延迟

# ML Backend 配置
ML_BACKEND_URL = "http://localhost:9090"
ML_BACKEND_TITLE = "自动标注后端"
REUSE_EXISTING_BACKEND = True  # 是否重用已存在的后端
```

### 执行结果示例
```
📊 项目创建完成摘要
====================================
⏱️  总用时: 45.2秒
📁 扫描文件: 248个
✅ 创建项目: 245个
❌ 创建失败: 3个
📥 导入成功: 242个
💥 导入失败: 3个

🏷️ 创建的项目列表:
   ✅ [15] 应急预案_01-国家自然灾害救助应急预案
   ✅ [16] 应急预案_02-国家防汛抗旱应急预案
   ✅ [17] 法律法规_水污染防治法
   ...

📋 项目编号列表: [15, 16, 17, 18, ...]
```

## 二、项目查询与管理 🔍

### 功能特点
- 📋 **项目列表**：查看所有项目的详细信息
- 🔍 **信息显示**：项目 ID、名称、创建时间、任务数量等
- 💾 **导出保存**：将项目信息保存为 JSON 文件
- 🗑️ **删除管理**：支持单个和批量删除项目

### 使用方法

#### 交互式管理界面
```bash
python query_projects.py
```

#### 菜单选项
```
🚀 Label Studio 项目管理器
=========================================
1. 查看所有项目
2. 删除单个项目  
3. 批量删除项目
4. 退出
```

#### 编程方式调用
```python
from query_projects import LabelStudioProjectQuery

# 创建查询器实例
query = LabelStudioProjectQuery()

# 获取项目列表
projects = query.get_project_list()
query.display_projects(projects)

# 保存到文件
query.save_to_file(projects, "my_projects.json")
```

### 项目信息显示
```
📋 项目列表 (共 15 个)
=====================================
🆔 ID: 1  | 📝 应急预案_01-国家自然灾害救助应急预案
   📅 创建时间: 2025-01-28 10:30:15
   📊 任务数量: 1个
   🏷️ 标签数量: 0个

🆔 ID: 2  | 📝 法律法规_水污染防治法
   📅 创建时间: 2025-01-28 10:31:22
   📊 任务数量: 1个  
   🏷️ 标签数量: 3个
```

## 三、项目删除管理 🗑️

### 功能特点
- 🗑️ **单个删除**：删除指定 ID 的项目
- 🔄 **批量删除**：同时删除多个项目
- ⚠️ **安全确认**：删除前需要用户确认
- 📊 **删除统计**：显示删除成功和失败的统计信息

### 使用方法

#### 方法一：交互式删除
```bash
python query_projects.py
# 选择菜单选项 2 或 3
```

#### 方法二：编程方式删除
```python
from query_projects import delete_projects_by_list

# 删除指定项目 ID 列表
result = delete_projects_by_list([1, 3, 5], confirm=True)
print(f"成功删除: {result['success']}")
print(f"删除失败: {result['failed']}")
```

#### 方法三：修改脚本批量删除
编辑 `query_projects.py` 文件末尾：
```python
# 删除项目 ID 14-23
projects_to_delete = list(range(14, 24))
result = delete_projects_by_list(projects_to_delete, confirm=True)
```

### 删除操作示例
```
🗑️ 准备删除以下 3 个项目:
   - ID: 1, 名称: 应急预案_01-国家自然灾害救助应急预案
   - ID: 3, 名称: 法律法规_水污染防治法  
   - ID: 5, 名称: 事故信息_flood_case

⚠️  警告：此操作将永久删除这些项目及其所有数据！
确认删除吗？(y/N): y

🚀 开始批量删除 3 个项目...
📋 进度: 1/3 - 删除项目 1
✅ 项目 1 删除成功
📋 进度: 2/3 - 删除项目 3  
✅ 项目 3 删除成功
📋 进度: 3/3 - 删除项目 5
✅ 项目 5 删除成功

📊 批量删除完成！
   - 成功删除: 3 个项目
   - 删除失败: 0 个项目
```

## 四、自动标注功能 🤖

### 功能特点
- 🎯 **智能预标注**：基于预训练模型的命名实体识别
- 🔄 **批量处理**：支持批量自动标注多个项目
- ⚙️ **配置灵活**：支持多种实体类型和标注策略
- 📊 **进度跟踪**：实时显示标注进度

### 使用方法
```bash
python auto_serial_labeler.py
```

### 支持的实体类型
基于 `entity_config.py` 和 `entity_config_flood_optimized.py` 配置：

#### 通用实体类型
- **PERSON** - 人名
- **ORG** - 组织机构名  
- **LOC** - 地点
- **TIME** - 时间
- **DISASTER** - 灾害事件

#### 防洪专业实体类型
- **WATER_LEVEL** - 水位信息
- **RAINFALL** - 降雨量
- **FLOOD_CONTROL** - 防洪措施
- **EMERGENCY_RESPONSE** - 应急响应
- **RISK_AREA** - 风险区域

### 标注配置
标注配置定义在 `文本命名实体提取标签.md` 文件中：
```xml
<View>
  <Text name="text" value="$text"/>
  <Labels name="label" toName="text">
    <Label value="PERSON" background="red"/>
    <Label value="ORG" background="blue"/>
    <Label value="LOC" background="green"/>
    <Label value="TIME" background="orange"/>
    <!-- 更多标签定义... -->
  </Labels>
</View>
```

## 📊 日志和监控

### 日志文件
所有操作都会生成详细日志，保存在 `logs/` 目录：
- `project_creator_YYYYMMDD_HHMMSS.log` - 项目创建日志
- `auto_labeler_YYYYMMDD_HHMMSS.log` - 自动标注日志

### 日志级别
- **INFO** - 常规操作信息
- **WARNING** - 警告信息
- **ERROR** - 错误信息
- **DEBUG** - 调试信息

### 监控输出示例
```
2025-01-28 10:30:15 - INFO - 🔗 正在连接Label Studio...
2025-01-28 10:30:16 - INFO - ✅ 连接成功
2025-01-28 10:30:16 - INFO - 📁 开始扫描文件: inputfile
2025-01-28 10:30:17 - INFO - 🔍 找到248个txt文件
2025-01-28 10:30:18 - INFO - 🏗️ 创建项目: 应急预案_01-国家自然灾害救助应急预案
2025-01-28 10:30:19 - INFO - ✅ 项目创建成功，ID: 15
```

## ⚙️ 高级配置

### 性能优化
```python
# 请求延迟配置（避免服务器过载）
DELAY_BETWEEN_REQUESTS = 0.5  # 秒

# 连接超时配置
ML_BACKEND_TIMEOUT = 30  # 秒
REQUEST_TIMEOUT = 15  # 秒

# 批处理大小
BATCH_SIZE = 10  # 每批处理的项目数量
```

### 自定义配置
```python
# 项目描述模板
PROJECT_DESCRIPTION_TEMPLATE = "基于{filename}的{task_type}项目，创建于{date}"

# 文件过滤规则
INCLUDE_EXTENSIONS = ['.txt']  # 包含的文件扩展名
EXCLUDE_PATTERNS = ['temp_', 'backup_']  # 排除的文件名模式

# ML Backend 配置
REUSE_EXISTING_BACKEND = True  # 重用已存在的后端
CREATE_PROJECT_SPECIFIC_BACKEND = False  # 为每个项目创建专用后端
```

## 🚨 故障排除

### 常见问题及解决方案

#### 1. API 令牌错误
**问题**: `401 Unauthorized` 错误
**解决**: 
- 检查 API 令牌是否正确
- 确认令牌具有足够权限
- 重新获取新的 API 令牌

#### 2. 服务连接失败
**问题**: `Connection refused` 或超时错误
**解决**:
- 确认 Label Studio 服务正在运行 (端口 8080)
- 确认 ML Backend 服务正在运行 (端口 9090)
- 检查防火墙设置

#### 3. 文件编码问题
**问题**: 导入文档时出现乱码
**解决**:
- 确保 txt 文件使用 UTF-8 编码
- 使用文本编辑器转换文件编码
- 检查文件是否包含特殊字符

#### 4. 项目创建失败
**问题**: 部分项目创建失败
**解决**:
- 查看详细日志了解失败原因
- 检查项目名称是否包含特殊字符
- 确认磁盘空间充足

#### 5. ML Backend 连接失败
**问题**: 自动标注功能不可用
**解决**:
- 确认 ML Backend 服务状态
- 检查模型文件是否完整
- 验证 Backend URL 配置

### 日志诊断
查看详细错误信息：
```bash
# 查看最新日志
tail -f logs/project_creator_*.log

# 搜索错误信息
grep "ERROR" logs/*.log

# 查看特定时间段的日志
grep "2025-01-28 10:" logs/project_creator_*.log
```

## 🔧 开发和扩展

### 代码结构
```
label-studio-ml-backend/my_ml_backend/
├── auto_project_creator.py      # 项目创建核心逻辑
├── query_projects.py           # 项目查询和管理
├── run_project_creator.py      # 快速启动脚本
├── auto_serial_labeler.py      # 自动标注器
├── entity_config.py           # 实体配置
├── model.py                   # ML 模型接口
└── processing_config.py       # 处理配置
```

### 自定义开发
1. **添加新的实体类型**：修改 `entity_config.py`
2. **自定义项目模板**：修改标注配置文件
3. **扩展处理逻辑**：继承现有类并重写方法
4. **集成其他服务**：修改 API 接口部分

### API 接口
主要使用的 Label Studio API 端点：
- `GET /api/projects/` - 获取项目列表
- `POST /api/projects/` - 创建项目
- `DELETE /api/projects/{id}/` - 删除项目
- `POST /api/projects/{id}/import` - 导入数据
- `GET /api/ml/` - 获取 ML Backend 列表
- `POST /api/ml/` - 创建 ML Backend

## 📞 技术支持

### 获取帮助
遇到问题时，请按以下顺序排查：

1. **查看日志文件** - 包含详细的错误信息和执行过程
2. **确认服务状态** - 验证 Label Studio 和 ML Backend 正常运行
3. **检查配置文件** - 确认所有配置参数正确
4. **验证权限设置** - 确保 API 令牌具有必要权限
5. **测试网络连接** - 确保程序能访问各项服务

### 性能建议
- 对于大量文件，建议分批次处理
- 适当调整请求延迟避免服务器过载
- 定期清理不需要的项目和日志文件
- 监控磁盘空间和内存使用情况

### 最佳实践
1. **备份重要数据** - 在批量操作前备份项目数据
2. **测试配置** - 先用少量文件测试配置正确性
3. **监控日志** - 定期查看日志了解系统状态
4. **版本控制** - 对配置文件进行版本管理
5. **文档更新** - 根据实际使用情况更新配置文档

---

## 📋 快速参考

### 常用命令
```bash
# 项目创建
python run_project_creator.py
python auto_project_creator.py

# 项目管理
python query_projects.py

# 自动标注
python auto_serial_labeler.py

# 查看日志
tail -f logs/*.log
```

### 重要文件路径
- 配置文件: `文本命名实体提取标签.md`
- 输入目录: `inputfile/`
- 日志目录: `logs/`
- 项目数据: `labelstudio_projects.json`

### 默认端口
- Label Studio: `http://localhost:8080`
- ML Backend: `http://localhost:9090`

---

*📝 最后更新：2025-01-28*
*✨ 版本：1.0.0*
*👨‍💻 维护者：AI Assistant*
