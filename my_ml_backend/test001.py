from openai import OpenAI

client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key='ms-ca41cec5-48ca-4a9e-9fdf-ac348a638d11', # ModelScope Token
)

response = client.chat.completions.create(
    model='Qwen/Qwen3-235B-A22B-Thinking-2507', # ModelScope Model-Id, required
    messages=[
        {
            'role': 'user',
            'content': '你好,你是什么模型'
        }
    ],
    stream=True
)
done_reasoning = False
for chunk in response:
    reasoning_chunk = chunk.choices[0].delta.reasoning_content
    answer_chunk = chunk.choices[0].delta.content
    if reasoning_chunk != '':
        print(reasoning_chunk, end='',flush=True)
    elif answer_chunk != '':
        if not done_reasoning:
            print('\n\n === Final Answer ===\n')
            done_reasoning = True
        print(answer_chunk, end='',flush=True)