#!/usr/bin/env python3
"""
测试修复后的推理模型处理逻辑
"""

import sys
import os
import json
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openai import OpenAI

def test_thinking_model_streaming():
    """测试推理模型的流式处理"""
    print("🧪 测试推理模型的流式处理修复...")
    
    # 配置API
    api_base_url = 'https://api-inference.modelscope.cn/v1'
    api_key = 'ms-b980f2d1-86e3-43bc-a72e-30c6849b3148'
    thinking_model = 'Qwen/Qwen3-235B-A22B-Thinking-2507'
    
    client = OpenAI(
        base_url=api_base_url,
        api_key=api_key,
        max_retries=0,
        timeout=250.0
    )
    
    # 简单的测试文本
    test_text = "根据《防洪法》第十条规定，水利部负责全国防汛工作。"
    
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
    
    print(f"🔍 测试推理模型: {thinking_model.split('/')[-1]}")
    print("=" * 60)
    
    try:
        start_time = time.time()
        
        # 使用流式处理
        response = client.chat.completions.create(
            model=thinking_model,
            messages=[
                {"role": "system", "content": "你是一个专业的命名实体识别专家。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.1,
            top_p=0.9,
            stream=True,  # 关键：使用流式
            timeout=250
        )
        
        reasoning_content = ""
        answer_content = ""
        done_reasoning = False
        
        print("📡 开始接收流式响应...")
        
        for chunk in response:
            # 检查推理内容
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                reasoning_chunk = chunk.choices[0].delta.reasoning_content
                reasoning_content += reasoning_chunk
                print("🧠", end="", flush=True)  # 显示推理进度
                
            # 检查答案内容
            elif hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                answer_chunk = chunk.choices[0].delta.content
                if not done_reasoning:
                    print("\n\n=== 推理完成，开始输出最终答案 ===")
                    done_reasoning = True
                answer_content += answer_chunk
                print("📝", end="", flush=True)  # 显示答案进度
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n\n⏰ 总耗时: {duration:.2f}秒")
        print(f"🧠 推理内容长度: {len(reasoning_content)}字符")
        print(f"📝 答案内容长度: {len(answer_content)}字符")
        
        # 分析结果
        if answer_content.strip():
            print("\n📄 最终答案内容:")
            print("-" * 50)
            print(answer_content)
            print("-" * 50)
            
            # 尝试解析JSON
            try_parse_result(answer_content, "最终答案")
            
        elif reasoning_content.strip():
            print("\n🧠 推理内容（未输出最终答案）:")
            print("-" * 50)
            print(reasoning_content[-500:])  # 显示最后500字符
            print("-" * 50)
            
            # 从推理内容中提取答案
            extracted_answer = extract_answer_from_reasoning(reasoning_content)
            if extracted_answer:
                print("\n🔍 从推理内容中提取的答案:")
                print("-" * 30)
                print(extracted_answer)
                print("-" * 30)
                try_parse_result(extracted_answer, "提取的答案")
        else:
            print("❌ 没有接收到任何内容")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def try_parse_result(content: str, content_type: str):
    """尝试解析结果"""
    print(f"\n🔧 解析{content_type}中的JSON:")
    
    import re
    
    # 策略1: 直接解析
    try:
        data = json.loads(content.strip())
        print("   ✅ 直接解析成功")
        show_entities(data)
        return
    except json.JSONDecodeError:
        print("   ❌ 直接解析失败")
    
    # 策略2: 提取```json代码块
    json_code_blocks = re.findall(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_code_blocks:
        for i, block in enumerate(json_code_blocks):
            try:
                data = json.loads(block)
                print(f"   ✅ JSON代码块{i+1}解析成功")
                show_entities(data)
                return
            except json.JSONDecodeError:
                print(f"   ❌ JSON代码块{i+1}解析失败")
    
    # 策略3: 提取JSON对象
    json_blocks = re.findall(r'\{[^{}]*\}', content, re.DOTALL)
    if json_blocks:
        for i, block in enumerate(json_blocks):
            try:
                data = json.loads(block)
                print(f"   ✅ JSON对象{i+1}解析成功")
                show_entities(data)
                return
            except json.JSONDecodeError:
                print(f"   ❌ JSON对象{i+1}解析失败")
    
    print("   ❌ 所有解析策略都失败")

def show_entities(data):
    """显示实体信息"""
    if isinstance(data, dict) and 'entities' in data:
        entities = data['entities']
        if isinstance(entities, list):
            print(f"      📊 识别到 {len(entities)} 个实体:")
            for i, entity in enumerate(entities):
                if isinstance(entity, dict):
                    text = entity.get('text', 'N/A')
                    label = entity.get('label', 'N/A')
                    start = entity.get('start', 'N/A')
                    end = entity.get('end', 'N/A')
                    print(f"         {i+1}. {text} ({label}) [{start}:{end}]")
        else:
            print("      ❌ entities不是列表格式")
    else:
        print(f"      ❌ 数据格式不正确: {type(data)}")

def extract_answer_from_reasoning(reasoning_content: str) -> str:
    """从推理内容中提取最终答案"""
    import re
    
    # 尝试提取JSON部分
    json_patterns = [
        r'```json\s*(.*?)\s*```',  # ```json 代码块
        r'\{[^{}]*"entities"[^{}]*:.*?\}',  # entities JSON
        r'\{.*?"entities".*?\}',  # 宽松的entities匹配
        r'\{.*\}',  # 最后的JSON匹配
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, reasoning_content, re.DOTALL)
        if matches:
            # 返回最后一个匹配的JSON（通常是最终结果）
            return matches[-1].strip()
    
    # 如果没有找到JSON，返回推理内容的后半部分
    lines = reasoning_content.strip().split('\n')
    if len(lines) > 10:
        return '\n'.join(lines[-5:])  # 返回最后5行
    
    return reasoning_content.strip()

if __name__ == "__main__":
    test_thinking_model_streaming()
