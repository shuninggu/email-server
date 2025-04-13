import pandas as pd
import re
import json

# 读取原始数据文件（请确保路径正确）
input_file = "enron/enron_gpt4_prompt8_gpt4o.xlsx"
df = pd.read_excel(input_file)

# 定义需要进行正则匹配的模型输出列名称
# 这里假设这5列分别为：
# model_columns = [ 
#     "Private_gemma:2b", 
#     "Private_llama3.2:3b", 
#     "Private_gemma3",
#     "Private_mistral",
#     "Private_llama3.2:1b",
#     "Private_qwen2.5:3b",
#     "Private_GPT4"
# ]

# # 定义新列的名称，新列将在新Excel文件中作为第9-13列输出
# new_columns = [
#     "Extracted_gemma:2b", 
#     "Extracted_llama3.2:3b", 
#     "Extracted_gemma3", 
#     "Extracted_mistral", 
#     "Extracted_llama3.2:1b", 
#     "Extracted_qwen2.5:3b",
#     "Extracted_GPT4",
    
# ]

model_columns = [ 
    "Private_GPT4"
]

# 定义新列的名称，新列将在新Excel文件中作为第9-13列输出
new_columns = [
    "Extracted_GPT4o",
    
]

# 定义正则表达式模式，匹配形如："some key" 可能有空格冒号可能有空格 "some value"
pattern = re.compile(r'"([^"]+)"\s*:\s*"([^"]+)"')

def extract_values(text):
    """
    从输入文本中提取所有匹配的格式："key" : "value"。
    返回一个字符串形式的列表，如：["private value 1", "private value 2", ...]。
    如果没有匹配到，则返回字符串 "None"。
    """
    # 如果数据为空，直接返回 "None"
    if pd.isnull(text):
        return "None"
    
    # 在文本中查找所有符合模式的匹配项
    matches = pattern.findall(text)
    
    # 若找到匹配项，则提取每个匹配项的第二个子组（即 value 部分）
    if matches:
        values = [match[1] for match in matches]
        # return str(values)  # 此处转换为字符串，也可以用 json.dumps(values) 保持json格式
        return json.dumps(values)
    else:
        return "None"

# 针对每个模型输出列进行正则提取，并存入新列
for old_col, new_col in zip(model_columns, new_columns):
    df[new_col] = df[old_col].apply(extract_values)

# 保存结果到新的Excel文件中
output_file = "enron/prompt9_3_extracted.xlsx"
df.to_excel(output_file, index=False)

print(f"提取完成，新文件保存为 {output_file}")
