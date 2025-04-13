import subprocess
import time
import pandas as pd

# ------------------------------------------------------------------------------
# 1) 配置部分
# ------------------------------------------------------------------------------
# 输入输出文件
input_file = "enron_labeled.xlsx"
output_file = "all/privacy_with_time.xlsx"  # 输出文件名稍作修改

PROMPT_TEMPLATE_8 = """In the following sentence, please convert all mentions of specific names, specific places, and numbers that may be sensitive into a format that represents the type of information they belong to.
Format requirements:
1. Always use double quotes for both keys and values: "key": "value"
2. Keep the rest of the sentence unchanged
3. Place the key-value pair exactly where the original information appears

You may select keys from the following list: Person Name, Email Address, Phone Number, Physical Address, password, Job Title, Organization, important time;

Here's an Example:
Input: Please write a greeting card for Nancy and her email address is nancy@gmail.com.
Output: Please write a greeting card for "name": "Nancy" and her email address is "email address": "nancy@gmail.com".

Note: Every piece of sensitive information MUST be converted to "key": "value" format with double quotes. If not applicable, return "None". Don't use the example in the real output, just follow the format.
Real Input:
{}

Real Output:

"""

# Prompt 模板（示例模板）
# PROMPT_TEMPLATE_9 = """Convert all sensitive information in the following sentence into "key": "value" format (using double quotes for both keys and values) without altering the rest of the text.

# Sensitive data includes:
# 1. Context-dependent items: Person Name, Email Address, Physical Address, Organization, Job Title, username...
# 2. Long integers: Phone Number, password, money, important time...

# If none is found, return "None".

# Here's an Example:
# Input: John, Please write a greeting card to nancy@gmail.com. Phillip
# Output: "name": "John", Please write a greeting card to "email address": "nancy@gmail.com". "name": "Phillip"

# Real Input:
# {}

# Real Output:
# """

# 本地模型列表（更新后的模型名称列表）
model_list = [
    "gemma3:1b",
    "gemma:2b",
    "llama3.2:3b",
    "mistral"
]

# 存储模型回复的列名
output_col_names = [
    "Private_gemma3:1b",
    "Private_gemma:2b",
    "Private_llama3.2:3b",
    "Private_mistral"
]

# 存储每个模型处理时间的列名
time_col_names = [
    "Time_gemma3:1b",
    "Time_gemma:2b",
    "Time_llama3.2:3b",
    "Time_mistral"
]

# ------------------------------------------------------------------------------
# 2) 读取 Excel 文件
# ------------------------------------------------------------------------------
df = pd.read_excel(input_file, dtype=str)
num_rows = len(df)

# 确保每个模型回复的列存在于 DataFrame 中
for col_name in output_col_names:
    if col_name not in df.columns:
        df[col_name] = ""

# 确保每个时间记录的列存在于 DataFrame 中
for col_name in time_col_names:
    if col_name not in df.columns:
        df[col_name] = ""

# ------------------------------------------------------------------------------
# 3) 定义调用本地模型的函数
# ------------------------------------------------------------------------------
def call_llama_local(model_name: str, email_body: str) -> str:
    """
    通过 `ollama run <model_name>` 调用指定的本地 LLM 模型，并返回模型的输出结果。
    """
    prompt = PROMPT_TEMPLATE_8.format(email_body)
    process = subprocess.run(
        ["ollama", "run", model_name],
        input=prompt,
        text=True,
        capture_output=True
    )
    return process.stdout.strip()

# ------------------------------------------------------------------------------
# 4) 处理每一行数据并统计处理时间，每处理10行写入一次Excel文件
# ------------------------------------------------------------------------------
start_time = time.time()

# 控制要处理的行数，这里取前 105 行或者较小者（可以根据需要修改）
rows_to_process = min(105, num_rows)

for idx in range(rows_to_process):
    # 假定数据中的文本位于第一列，如果为空则赋空字符串
    email_text = df.iloc[idx, 0] if pd.notna(df.iloc[idx, 0]) else ""
    
    # 针对每个模型调用处理，并记录返回结果及处理时间
    for model_name, out_col, time_col in zip(model_list, output_col_names, time_col_names):
        row_start_time = time.time()  # 记录开始时间
        model_response = call_llama_local(model_name, email_text)
        row_end_time = time.time()    # 记录结束时间
        elapsed_time = row_end_time - row_start_time  # 计算耗时
        
        # 将模型的回复和处理时间分别保存到 DataFrame 对应的列中
        df.at[idx, out_col] = model_response
        df.at[idx, time_col] = f"{elapsed_time:.2f}"  # 保留两位小数
        
        print(f"处理第 {idx} 行数据，模型 {model_name} 用时: {elapsed_time:.2f} 秒")
    
    # 每处理10行写一次文件，或者最后一行也写入
    if (idx + 1) % 10 == 0 or (idx + 1) == rows_to_process:
        df.to_excel(output_file, index=False)
        print(f"Checkpoint: 已写入 {idx + 1} 行数据到 {output_file}")

end_time = time.time()
total_time = end_time - start_time
avg_time_per_row = total_time / rows_to_process if rows_to_process > 0 else 0

# ------------------------------------------------------------------------------
# 5) 输出统计信息
# ------------------------------------------------------------------------------
print(f"\n共处理 {rows_to_process} 行数据。")
print(f"总执行时间: {total_time:.2f} 秒。")
print(f"平均每行处理时间: {avg_time_per_row:.2f} 秒。")
print(f"最终更新后的文件已保存到: {output_file}")
