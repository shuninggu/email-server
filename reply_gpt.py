import pandas as pd
import time
import os
import openai

# 设置 OpenAI API 密钥，从环境变量中获取
openai.api_key = os.getenv("OPENAI_API_KEY")

# 文件路径
input_file = "gemma27b/mask_prompt.xlsx"   # 输入 Excel 文件
output_file = "gemma27b/with_remote_reply.xlsx"           # 输出 Excel 文件

# 定义提示模板：
# 系统要求仅返回邮件正文，不包含推理过程
PROMPT_TEMPLATE = """You are a helpful email assistant. I have just received the following email. 
Please generate a reply for me. Only return the email body without reasoning.
Email:
{}
===================="""

# 指定 GPT-4o 模型（如有需要，请更新模型名称）
model_gpt4o = "gpt-4o"

# 定义输入和输出列名称
col_input = "masked_prompt"
col_output = "masked_reply"

# ------------------------------------------------------------------------------
# 1) 读取 Excel 文件
# ------------------------------------------------------------------------------
df = pd.read_excel(input_file, dtype=str)

# 如果输出列不存在，则添加该列
if col_output not in df.columns:
    df[col_output] = ""

# ------------------------------------------------------------------------------
# 2) 定义调用 OpenAI Chat API 的函数
# ------------------------------------------------------------------------------
def call_openai_chat(model_name: str, content: str) -> str:
    """
    调用 OpenAI Chat API 并返回响应的文本。
    """
    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are ChatGPT."},
                {"role": "user", "content": content}
            ],
            temperature=0.0,  # 设置为 0 以保证输出更确定
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI model {model_name}: {e}")
        return ""

# ------------------------------------------------------------------------------
# 3) 处理每一行数据并生成回复
# ------------------------------------------------------------------------------
start_time = time.time()
num_rows = len(df)

for idx in range(num_rows):
    # 从 "masked_prompt" 列获取邮件文本
    email_text = df.at[idx, col_input]
    if not isinstance(email_text, str):
        email_text = ""
    
    # 构建提示，将邮件文本嵌入提示模板
    prompt_text = PROMPT_TEMPLATE.format(email_text)
    
    # 调用 GPT-4o 生成回复
    row_start_time = time.time()
    reply_text = call_openai_chat(model_gpt4o, prompt_text)
    
    # 将生成的回复保存到 "reply_masked" 列中
    df.at[idx, col_output] = reply_text
    
    row_end_time = time.time()
    print(f"Processed row {idx+1}/{num_rows} in {row_end_time - row_start_time:.2f} seconds.")

# ------------------------------------------------------------------------------
# 4) 将结果保存到 Excel 文件
# ------------------------------------------------------------------------------
df.to_excel(output_file, index=False)
total_time = time.time() - start_time
print(f"\nFinished processing {num_rows} rows in {total_time:.2f} seconds.")
print(f"Output saved to {output_file}")
