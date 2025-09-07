#!/usr/bin/env python3
"""
测试Qwen3-235B-A22B-Thinking-2507推理模型的响应格式
专门分析推理模型的返回报文结构
"""

import sys
import os
import json
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openai import OpenAI

def test_thinking_model_response():
    """测试推理模型的实际响应格式"""
    print("🧪 测试Qwen3-235B-A22B-Thinking-2507推理模型响应格式...")
    
    # 配置API
    api_base_url = 'https://api-inference.modelscope.cn/v1'
    api_key = 'ms-b980f2d1-86e3-43bc-a72e-30c6849b3148'  # 第一个API Key
    thinking_model = 'Qwen/Qwen3-235B-A22B-Thinking-2507'
    normal_model = 'deepseek-ai/DeepSeek-V3'
    
    client = OpenAI(
        base_url=api_base_url,
        api_key=api_key,
        max_retries=0,
        timeout=250.0
    )
    
    # 简单的测试文本
    test_text = "根据《防洪法》第十条规定，水利部负责全国防汛工作。"
    
    # 简化的提示词
    prompt = f"""请对以下文本进行命名实体识别：
{test_text}

请严格按照以下JSON格式返回结果：
{{
  "entities": [
    {{
      "text": "实体文本",
      "start": 起始位置,
      "end": 结束位置,
      "label": "实体类型"
    }}
  ]
}}

请识别法律条款、政府机构等实体。"""
    
    # 测试两个模型的响应格式
    models_to_test = [
        (thinking_model, "推理模型"),
        (normal_model, "普通模型")
    ]
    
    for model, model_type in models_to_test:
        print(f"\n🔍 测试 {model_type}: {model.split('/')[-1]}")
        print("=" * 60)
        
        try:
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的命名实体识别专家。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1,
                top_p=0.9,
                stream=False,
                timeout=250
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏰ 响应时间: {duration:.2f}秒")
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                print(f"📏 响应长度: {len(content) if content else 0}字符")
                
                if content:
                    print(f"\n📄 原始响应内容:")
                    print("-" * 50)
                    print(content)
                    print("-" * 50)
                    
                    # 分析响应结构
                    analyze_response_structure(content, model_type)
                    
                    # 尝试解析JSON
                    try_parse_json(content, model_type)
                    
                else:
                    print("❌ 响应内容为空")
            else:
                print("❌ 响应格式异常，没有choices")
                
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")

def analyze_response_structure(content: str, model_type: str):
    """分析响应的结构特征"""
    print(f"\n🔍 {model_type}响应结构分析:")
    
    # 检查是否包含思维过程
    thinking_indicators = [
        "<thinking>", "</thinking>",
        "思考过程", "推理过程", "分析过程",
        "让我来分析", "首先", "然后", "最后",
        "我需要", "应该识别"
    ]
    
    has_thinking = any(indicator in content for indicator in thinking_indicators)
    print(f"   🧠 是否包含思维过程: {'是' if has_thinking else '否'}")
    
    # 检查JSON结构
    import re
    json_matches = re.findall(r'\{[^{}]*\}', content, re.DOTALL)
    print(f"   📊 JSON块数量: {len(json_matches)}")
    
    # 检查entities字段
    entities_count = content.count('"entities"')
    print(f"   🏷️ entities字段出现次数: {entities_count}")
    
    # 检查是否有多段式回答
    lines = content.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    print(f"   📝 非空行数: {len(non_empty_lines)}")
    
    # 检查特殊标记
    special_markers = ['```', '```json', '<answer>', '</answer>', '<result>', '</result>']
    found_markers = [marker for marker in special_markers if marker in content]
    if found_markers:
        print(f"   🔖 特殊标记: {', '.join(found_markers)}")

def try_parse_json(content: str, model_type: str):
    """尝试解析JSON内容"""
    print(f"\n🔧 {model_type}JSON解析测试:")
    
    import re
    
    # 策略1: 直接解析
    try:
        data = json.loads(content.strip())
        print("   ✅ 策略1(直接解析): 成功")
        check_entities_structure(data)
        return data
    except json.JSONDecodeError as e:
        print(f"   ❌ 策略1(直接解析): 失败 - {e}")
    
    # 策略2: 提取最后一个JSON块
    json_blocks = re.findall(r'\{[^{}]*\}', content, re.DOTALL)
    if json_blocks:
        for i, block in enumerate(json_blocks):
            try:
                data = json.loads(block)
                print(f"   ✅ 策略2(JSON块{i+1}): 成功")
                check_entities_structure(data)
                return data
            except json.JSONDecodeError:
                print(f"   ❌ 策略2(JSON块{i+1}): 失败")
    
    # 策略3: 提取```json代码块
    json_code_blocks = re.findall(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_code_blocks:
        for i, block in enumerate(json_code_blocks):
            try:
                data = json.loads(block)
                print(f"   ✅ 策略3(代码块{i+1}): 成功")
                check_entities_structure(data)
                return data
            except json.JSONDecodeError:
                print(f"   ❌ 策略3(代码块{i+1}): 失败")
    
    # 策略4: 移除thinking标签后解析
    thinking_removed = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
    if thinking_removed.strip() != content.strip():
        try:
            data = json.loads(thinking_removed.strip())
            print("   ✅ 策略4(移除thinking): 成功")
            check_entities_structure(data)
            return data
        except json.JSONDecodeError:
            print("   ❌ 策略4(移除thinking): 失败")
    
    print("   ❌ 所有解析策略都失败")
    return None

def check_entities_structure(data):
    """检查解析出的数据结构"""
    if isinstance(data, dict):
        if 'entities' in data:
            entities = data['entities']
            if isinstance(entities, list):
                print(f"      📊 识别到 {len(entities)} 个实体")
                for i, entity in enumerate(entities[:3]):  # 只显示前3个
                    if isinstance(entity, dict):
                        text = entity.get('text', 'N/A')
                        label = entity.get('label', 'N/A')
                        start = entity.get('start', 'N/A')
                        end = entity.get('end', 'N/A')
                        print(f"         {i+1}. {text} ({label}) [{start}:{end}]")
            else:
                print("      ❌ entities不是列表格式")
        else:
            print("      ❌ 缺少entities字段")
            print(f"      📝 实际字段: {list(data.keys())}")
    else:
        print(f"      ❌ 根节点不是字典，而是: {type(data)}")

if __name__ == "__main__":
    test_thinking_model_response()
