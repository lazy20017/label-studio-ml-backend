#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests

def test_ml_backend_api():
    """测试ML Backend API"""
    
    # 模拟Label Studio的请求
    request_data = {
        "tasks": [{
            "id": 1,
            "data": {
                "captioning": "https://example.com/test.jpg"
            }
        }],
        "label_config": """
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
        """,
        "project": "test.1234567890",
        "params": {
            "context": {}
        }
    }
    
    # 发送请求到ML Backend
    try:
        response = requests.post(
            "http://localhost:9090/predict",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n=== API响应 ===")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 检查响应格式
            if 'results' in result:
                print("\n✅ 响应包含 'results' 字段")
                results = result['results']
                print(f"结果数量: {len(results)}")
                
                for i, prediction in enumerate(results):
                    print(f"\n--- 预测 {i+1} ---")
                    print(f"model_version: {prediction.get('model_version')}")
                    print(f"score: {prediction.get('score')}")
                    
                    if 'result' in prediction:
                        result_items = prediction['result']
                        print(f"result项目数量: {len(result_items)}")
                        
                        for j, item in enumerate(result_items):
                            print(f"  项目 {j+1}:")
                            print(f"    from_name: {item.get('from_name')}")
                            print(f"    to_name: {item.get('to_name')}")
                            print(f"    type: {item.get('type')}")
                            
                            if 'value' in item:
                                value = item['value']
                                if 'text' in value:
                                    text = value['text']
                                    print(f"    text类型: {type(text)}")
                                    print(f"    text内容: {text}")
            else:
                print("\n❌ 响应不包含 'results' 字段")
                print(f"响应键: {list(result.keys())}")
        else:
            print(f"\n❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到ML Backend，请确保服务正在运行")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_ml_backend_api() 