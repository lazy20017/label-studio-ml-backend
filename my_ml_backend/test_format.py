#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def test_json_format():
    """测试我们的JSON格式是否正确"""
    
    # 我们的预测结果格式
    our_prediction = {
        "model_version": "1.0.0-debug",
        "score": 0.95,
        "result": [
            {
                "from_name": "caption",
                "to_name": "image",
                "type": "textarea",
                "value": {
                    "text": ["这是一张图片的描述内容"]
                }
            }
        ]
    }
    
    # 官方示例格式
    official_prediction = {
        "model_version": "HuggingFaceLLM-v0.0.1",
        "score": 0.0,
        "result": [
            {
                "from_name": "generated_text",
                "to_name": "input_text",
                "type": "textarea",
                "value": {
                    "text": ['"I am not walking on air"\nI\'m not sure if you\'re being sarcastic or not, but I think you\'re right.']
                }
            }
        ]
    }
    
    print("=== 我们的格式 ===")
    print(json.dumps(our_prediction, indent=2, ensure_ascii=False))
    
    print("\n=== 官方示例格式 ===")
    print(json.dumps(official_prediction, indent=2, ensure_ascii=False))
    
    # 检查关键字段
    print("\n=== 格式对比 ===")
    print(f"我们的格式:")
    print(f"  - model_version: {our_prediction['model_version']}")
    print(f"  - score: {our_prediction['score']}")
    print(f"  - result[0].from_name: {our_prediction['result'][0]['from_name']}")
    print(f"  - result[0].to_name: {our_prediction['result'][0]['to_name']}")
    print(f"  - result[0].type: {our_prediction['result'][0]['type']}")
    print(f"  - result[0].value.text: {our_prediction['result'][0]['value']['text']}")
    print(f"  - result[0].value.text类型: {type(our_prediction['result'][0]['value']['text'])}")
    
    print(f"\n官方格式:")
    print(f"  - model_version: {official_prediction['model_version']}")
    print(f"  - score: {official_prediction['score']}")
    print(f"  - result[0].from_name: {official_prediction['result'][0]['from_name']}")
    print(f"  - result[0].to_name: {official_prediction['result'][0]['to_name']}")
    print(f"  - result[0].type: {official_prediction['result'][0]['type']}")
    print(f"  - result[0].value.text: {official_prediction['result'][0]['value']['text']}")
    print(f"  - result[0].value.text类型: {type(official_prediction['result'][0]['value']['text'])}")
    
    # 检查是否缺少必需字段
    required_fields = ['model_version', 'score', 'result']
    result_required_fields = ['from_name', 'to_name', 'type', 'value']
    value_required_fields = ['text']
    
    print("\n=== 字段检查 ===")
    for field in required_fields:
        if field in our_prediction:
            print(f"✅ {field}: 存在")
        else:
            print(f"❌ {field}: 缺失")
    
    if our_prediction['result']:
        for field in result_required_fields:
            if field in our_prediction['result'][0]:
                print(f"✅ result[0].{field}: 存在")
            else:
                print(f"❌ result[0].{field}: 缺失")
        
        for field in value_required_fields:
            if field in our_prediction['result'][0]['value']:
                print(f"✅ result[0].value.{field}: 存在")
            else:
                print(f"❌ result[0].value.{field}: 缺失")

if __name__ == "__main__":
    test_json_format() 