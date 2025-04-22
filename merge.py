# import re
# import json
# import pandas as pd
# import os

# def parse_key_value(text):
#     """
#     从 B 列文本中解析形如 "key" : "value" 的所有对，返回一个列表。
#     注意：
#       - 考虑冒号前后存在若干空格
#       - 只要匹配到 "..." : "..." 即可
#       - 如果同一个 value 多次出现，只保留第一次
#     """
#     if not isinstance(text, str):
#         return None
    
#     # 预编译一个正则，匹配 "key" : "value"
#     # 允许冒号前后若干空格/换行
#     pattern = re.compile(r'"([^"]+)"\s*:\s*"([^"]*)"')
    
#     matches = pattern.findall(text)
#     if not matches:
#         return None
    
#     # 做去重判断（针对 value）
#     # 如果出现同一个 value 多次，只保留第一次
#     seen_values = set()
#     result = []
#     idx = 1
#     for key, val in matches:
#         if val not in seen_values:
#             seen_values.add(val)
#             # 生成 replacedValue，如 [key_idx]
#             replaced_val = f"[{key}_{idx}]"
#             result.append({
#                 "id": idx,
#                 "key": key,
#                 "originalValue": val,
#                 "replacedValue": replaced_val
#             })
#             idx += 1
    
#     return result if result else None


# def mask_text(original_text, privacy_list):
#     """
#     将 original_text 中所有的 originalValue 替换成 replacedValue。
#     不做整词匹配，只要包含就替换。
#     privacy_list 结构类似：
#     [
#       {
#         "id": 1,
#         "key": "name",
#         "originalValue": "Annie",
#         "replacedValue": "[name_1]"
#       },
#       ...
#     ]
#     """
#     if not isinstance(original_text, str):
#         return original_text
#     if not privacy_list:
#         return original_text
    
#     masked_text = original_text
#     for item in privacy_list:
#         orig_val = item["originalValue"]
#         repl_val = item["replacedValue"]
#         if orig_val:
#             masked_text = masked_text.replace(orig_val, repl_val)
    
#     return masked_text


# def unmask_text(reply_mask_text, privacy_list):
#     """
#     对 GPT 返回的 reply_mask 进行还原：
#       - 找到其中所有方括号 [xxx_yy]
#       - 在 privacy_list 中匹配 replacedValue
#       - 用 originalValue 替换
#     """
#     if not isinstance(reply_mask_text, str):
#         return reply_mask_text
#     if not privacy_list:
#         return reply_mask_text
    
#     restored_text = reply_mask_text
    
#     # 用正则找到所有 [xxx_yy] 的片段
#     pattern = re.compile(r'\[([^\]]+)\]')
#     brackets = pattern.findall(reply_mask_text)
    
#     # 按照出现顺序，逐个替换
#     for br in brackets:
#         bracket_full = f"[{br}]"
#         # 在 privacy_list 中查找 replacedValue
#         for item in privacy_list:
#             if item["replacedValue"] == bracket_full:
#                 # 替换为 originalValue
#                 restored_text = restored_text.replace(bracket_full, item["originalValue"])
#                 break  # 找到后就跳出，避免重复替换
    
#     return restored_text


# def process_step1_mask(input_excel, output_excel):
#     """
#     第一步：读取 all/restore.xlsx，
#     解析 B 列 (Private_llama3.2:3b) -> 存到 storage_privacy.json
#     对 A 列 (body) 替换为 masked_prompt
#     输出到 all/restore_processed.xlsx
#     """
#     df = pd.read_excel(input_excel)
    
#     # 确保存在相应的列
#     if "Body" not in df.columns or "Private_qwen2.5:7b" not in df.columns:
#         raise ValueError("输入Excel缺少 body 或 Private_llama3.2:3b 列")
    
#     storage_col = "storage_privacy.json"
#     masked_col = "masked_prompt"
    
#     # 新增列，存储结果
#     df[storage_col] = None
#     df[masked_col] = None
    
#     for i in range(len(df)):
#         text_b = df.at[i, "Private_qwen2.5:7b"]
#         text_a = df.at[i, "Body"]
        
#         # 1) 解析 key-value
#         privacy_list = parse_key_value(text_b)
        
#         # 2) 如果解析到的列表不为空，写入 JSON，否则写 None
#         if privacy_list:
#             df.at[i, storage_col] = json.dumps(privacy_list, ensure_ascii=False)
#         else:
#             df.at[i, storage_col] = None
        
#         # 3) 替换 A 中出现的 originalValue -> replacedValue
#         if privacy_list:
#             masked = mask_text(text_a, privacy_list)
#         else:
#             masked = text_a
        
#         df.at[i, masked_col] = masked
    
#     # 输出到新的 Excel
#     df.to_excel(output_excel, index=False)
#     print(f"[STEP1] Done. Output -> {output_excel}")


# def process_step2_unmask(input_excel, output_excel):
#     """
#     第二步：读取上一步生成的 Excel (包含 reply_mask 列),
#     然后根据 storage_privacy.json 列做反向替换生成 restored_value 列
#     输出到 all/reply_restored.xlsx
#     """
#     df = pd.read_excel(input_excel)
    
#     storage_col = "storage_privacy.json"
#     reply_mask_col = "reply_mask"
#     restored_col = "restored_value"
    
#     # 确保存在 reply_mask 列和 storage_privacy.json 列
#     if reply_mask_col not in df.columns or storage_col not in df.columns:
#         raise ValueError(f"输入Excel缺少 {reply_mask_col} 或 {storage_col} 列")
    
#     df[restored_col] = None
    
#     for i in range(len(df)):
#         reply_text = df.at[i, reply_mask_col]
#         storage_json_str = df.at[i, storage_col]
        
#         if pd.isna(storage_json_str) or not isinstance(storage_json_str, str):
#             # 没有任何隐私信息记录，就直接复制 reply_mask 到 restored_value
#             df.at[i, restored_col] = reply_text
#             continue
        
#         # 解析成 list
#         try:
#             privacy_list = json.loads(storage_json_str)
#         except:
#             privacy_list = None
        
#         if not privacy_list:
#             df.at[i, restored_col] = reply_text
#             continue
        
#         # 反向还原
#         restored = unmask_text(reply_text, privacy_list)
#         df.at[i, restored_col] = restored
    
#     df.to_excel(output_excel, index=False)
#     print(f"[STEP2] Done. Output -> {output_excel}")


# if __name__ == "__main__":
#     # 假设第一步处理后得到 masked_prompt
#     # 在此示例中：
#     #   输入文件：all/restore.xlsx
#     #   输出文件：all/restore_processed.xlsx
#     process_step1_mask(
#         input_excel="all/qwen7b_detection.xlsx",
#         output_excel="all/qwen7b_masked.xlsx"
#     )
    
#     # 假设这里你用 masked_prompt 去调用 GPT-4o，拿到 reply_mask，
#     # 并将其写回到 all/restore_processed.xlsx 的 reply_mask 列
    
#     # 然后执行第二步从 reply_mask 生成 restored_value
#     # 输出最终文件：all/reply_restored.xlsx
#     process_step2_unmask(
#         input_excel="all/qwen7b_masked.xlsx",
#         output_excel="all/qweb7b_restored.xlsx"
#     )


import re
import json
import pandas as pd
import os

# 如果要实际调用 OpenAI，需要安装 openai：
#   pip install openai
# 并在程序里导入：
import openai

# 这里示例你可把 API Key 放到环境变量，或硬编码(不推荐)
# os.environ["OPENAI_API_KEY"] = "sk-xxxx"
# openai.api_key = os.getenv("OPENAI_API_KEY", "<YOUR_API_KEY_HERE>")
openai.api_key = os.getenv("OPENAI_API_KEY")

def call_gpt_api(prompt, model="gpt-4", temperature=0.0):
    """
    调用 GPT-4o 的一个简单封装示例。
    prompt: 要发送给 GPT 的文本
    model: 指定使用的模型, 如 'gpt-4'
    temperature: 多样性控制
    返回: GPT 生成的字符串
    """
    try:
        # 这里仅作示例，可根据你的实际需求补充 messages、system 提示等
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        reply_text = response["choices"][0]["message"]["content"]
        return reply_text.strip()
    except Exception as e:
        print(f"Error calling GPT API: {e}")
        return ""


def parse_key_value(text):
    """
    从 B 列文本中解析形如 "key" : "value" 的所有对，返回一个列表。
    注意：
      - 考虑冒号前后存在若干空格
      - 如果同一个 value 多次出现，只保留第一次
    """
    if not isinstance(text, str):
        return None
    
    pattern = re.compile(r'"([^"]+)"\s*:\s*"([^"]*)"')
    matches = pattern.findall(text)
    if not matches:
        return None
    
    seen_values = set()
    result = []
    idx = 1
    for key, val in matches:
        if val not in seen_values:
            seen_values.add(val)
            replaced_val = f"[{key}_{idx}]"
            result.append({
                "id": idx,
                "key": key,
                "originalValue": val,
                "replacedValue": replaced_val
            })
            idx += 1
    
    return result if result else None


def mask_text(original_text, privacy_list):
    """
    将 original_text 中所有的 originalValue 替换成 replacedValue。
    不做整词匹配，只要包含就替换。
    """
    if not isinstance(original_text, str):
        return original_text
    if not privacy_list:
        return original_text
    
    masked_text = original_text
    for item in privacy_list:
        orig_val = item["originalValue"]
        repl_val = item["replacedValue"]
        if orig_val:
            masked_text = masked_text.replace(orig_val, repl_val)
    
    return masked_text


def unmask_text(reply_mask_text, privacy_list):
    """
    对 GPT 返回的 reply_mask 进行还原：
      - 找到其中所有方括号 [xxx_yy]
      - 在 privacy_list 中匹配 replacedValue
      - 用 originalValue 替换
    """
    if not isinstance(reply_mask_text, str):
        return reply_mask_text
    if not privacy_list:
        return reply_mask_text
    
    restored_text = reply_mask_text
    
    pattern = re.compile(r'\[([^\]]+)\]')
    brackets = pattern.findall(reply_mask_text)
    
    for br in brackets:
        bracket_full = f"[{br}]"
        for item in privacy_list:
            if item["replacedValue"] == bracket_full:
                restored_text = restored_text.replace(bracket_full, item["originalValue"])
                break
    
    return restored_text


def main_pipeline(input_excel, output_excel_masked, output_excel_restored):
    """
    主流程:
      1. 读取 input_excel (all/qwen7b_detection.xlsx)
      2. 从 B 列解析 key-value 并生成 storage_privacy.json
      3. 对 A 列做替换生成 masked_prompt
      4. 调用 GPT 并写入 reply_mask
      5. 反向还原 -> restored_value
      6. 输出最终到 output_excel_restored
    其中我们会在中间把含有 masked_prompt, reply_mask 等列暂存到 output_excel_masked
    """
    df = pd.read_excel(input_excel)
    
    # 确保列名和你的 Excel 中保持一致
    col_a = "Body"
    col_b = "Private_qwen2.5:7b"
    col_storage = "storage_privacy.json"
    col_masked = "masked_prompt"
    col_reply = "reply_mask"
    col_restored = "restored_value"
    
    if col_a not in df.columns or col_b not in df.columns:
        raise ValueError(f"输入Excel缺少 {col_a} 或 {col_b} 列")
    
    # 初始化新列
    df[col_storage] = None
    df[col_masked] = None
    df[col_reply] = None
    df[col_restored] = None
    
    # 1) 解析 B 列、存储 privacy_list
    # 2) 将 A 列文本替换 -> masked_prompt
    # 3) 调用 GPT -> reply_mask
    for i in range(len(df)):
        text_b = df.at[i, col_b]
        text_a = df.at[i, col_a]
        
        privacy_list = parse_key_value(text_b)
        if privacy_list:
            df.at[i, col_storage] = json.dumps(privacy_list, ensure_ascii=False)
        else:
            df.at[i, col_storage] = None
        
        if privacy_list:
            masked = mask_text(text_a, privacy_list)
        else:
            masked = text_a
        
        df.at[i, col_masked] = masked
        
        # 调用 GPT 并将结果写到 reply_mask 列
        # 如果你不想每一行都调用 GPT，可以根据需要做批量处理
        if masked and isinstance(masked, str) and masked.strip():
            gpt_reply = call_gpt_api(masked)  # 这里就是向 GPT-4o 发送 masked_prompt
            df.at[i, col_reply] = gpt_reply
        else:
            df.at[i, col_reply] = ""
    
    # 先把带有 reply_mask 的结果暂存输出
    df.to_excel(output_excel_masked, index=False)
    print(f"[STEP] Masked + GPT reply -> {output_excel_masked}")
    
    # 4) 反向还原
    for i in range(len(df)):
        storage_json_str = df.at[i, col_storage]
        reply_text = df.at[i, col_reply]
        
        if not storage_json_str or pd.isna(storage_json_str):
            # 没有隐私信息
            df.at[i, col_restored] = reply_text
            continue
        
        try:
            privacy_list = json.loads(storage_json_str)
        except:
            privacy_list = None
        
        if not privacy_list:
            df.at[i, col_restored] = reply_text
            continue
        
        # 调用反向还原
        restored_val = unmask_text(reply_text, privacy_list)
        df.at[i, col_restored] = restored_val
    
    # 最终输出含 restored_value 的文件
    df.to_excel(output_excel_restored, index=False)
    print(f"[STEP] Restored -> {output_excel_restored}")


if __name__ == "__main__":
    # 以你的文件路径为例
    input_file = "all/qwen7b_detection.xlsx"
    output_masked_file = "all/qwen7b_masked.xlsx"
    output_restored_file = "all/qwen7b_restored.xlsx"
    
    main_pipeline(input_file, output_masked_file, output_restored_file)
