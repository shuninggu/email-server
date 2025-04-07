# import torch
# from transformers import AutoTokenizer, AutoModelForTokenClassification

# # 模型名称（HuggingFace上提供）
# model_name = "iiiorg/piiranha-v1-detect-personal-information"

# # 加载模型和分词器
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForTokenClassification.from_pretrained(model_name)

# # 自动检测设备（GPU or CPU）
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# model.to(device)

# def mask_pii(text, aggregate_redaction=True):
#     inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
#     inputs = {k: v.to(device) for k, v in inputs.items()}

#     with torch.no_grad():
#         outputs = model(**inputs)

#     predictions = torch.argmax(outputs.logits, dim=-1)
#     encoded_inputs = tokenizer.encode_plus(text, return_offsets_mapping=True, add_special_tokens=True)
#     offset_mapping = encoded_inputs['offset_mapping']

#     masked_text = list(text)
#     is_redacting = False
#     redaction_start = 0
#     current_pii_type = ''

#     for i, (start, end) in enumerate(offset_mapping):
#         if start == end:
#             continue
#         label = predictions[0][i].item()
#         if label != model.config.label2id['O']:
#             pii_type = model.config.id2label[label]
#             if not is_redacting:
#                 is_redacting = True
#                 redaction_start = start
#                 current_pii_type = pii_type
#             elif not aggregate_redaction and pii_type != current_pii_type:
#                 apply_redaction(masked_text, redaction_start, start, current_pii_type, aggregate_redaction)
#                 redaction_start = start
#                 current_pii_type = pii_type
#         else:
#             if is_redacting:
#                 apply_redaction(masked_text, redaction_start, end, current_pii_type, aggregate_redaction)
#                 is_redacting = False

#     if is_redacting:
#         apply_redaction(masked_text, redaction_start, len(masked_text), current_pii_type, aggregate_redaction)

#     return ''.join(masked_text)

# def apply_redaction(masked_text, start, end, pii_type, aggregate_redaction):
#     for j in range(start, end):
#         masked_text[j] = ''
#     if aggregate_redaction:
#         masked_text[start] = '[redacted]'
#     else:
#         masked_text[start] = f'[{pii_type}]'

# # 示例文本
# example_text = "My name is Dhanushkumar and I live at Chennai. My phone number is +9190803470."

# # 调用函数
# print("Aggregated redaction:")
# print(mask_pii(example_text, aggregate_redaction=True))

# print("\nDetailed redaction:")
# print(mask_pii(example_text, aggregate_redaction=False))













import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForTokenClassification
from tqdm import tqdm

# 模型和设备配置
model_name = "iiiorg/piiranha-v1-detect-personal-information"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# PII 遮盖函数
def mask_pii(text, aggregate_redaction=True):
    if not isinstance(text, str) or text.strip() == "":
        return ""  # 跳过空文本
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=-1)
    encoded_inputs = tokenizer.encode_plus(text, return_offsets_mapping=True, add_special_tokens=True)
    offset_mapping = encoded_inputs['offset_mapping']

    masked_text = list(text)
    is_redacting = False
    redaction_start = 0
    current_pii_type = ''

    for i, (start, end) in enumerate(offset_mapping):
        if start == end:
            continue
        label = predictions[0][i].item()
        if label != model.config.label2id['O']:
            pii_type = model.config.id2label[label]
            if not is_redacting:
                is_redacting = True
                redaction_start = start
                current_pii_type = pii_type
            elif not aggregate_redaction and pii_type != current_pii_type:
                apply_redaction(masked_text, redaction_start, start, current_pii_type, aggregate_redaction)
                redaction_start = start
                current_pii_type = pii_type
        else:
            if is_redacting:
                apply_redaction(masked_text, redaction_start, end, current_pii_type, aggregate_redaction)
                is_redacting = False
    if is_redacting:
        apply_redaction(masked_text, redaction_start, len(masked_text), current_pii_type, aggregate_redaction)
    return ''.join(masked_text)

def apply_redaction(masked_text, start, end, pii_type, aggregate_redaction):
    for j in range(start, end):
        masked_text[j] = ''
    if aggregate_redaction:
        masked_text[start] = '[redacted]'
    else:
        masked_text[start] = f'[{pii_type}]'

# === 主逻辑：加载 CSV 并处理 ===
input_path = "pbe/pbe_top100.csv"
output_path = "pbe/pbe_top100_masked.csv"

df = pd.read_csv(input_path)

# 如果没有列名，假设第一列是邮件内容
if df.columns[0] != "text":
    df.rename(columns={df.columns[0]: "text"}, inplace=True)

print("正在处理数据，共有行数:", len(df))

# 创建新的列 masked_text，处理第一列 text
tqdm.pandas()
df["masked_text"] = df["text"].progress_apply(lambda x: mask_pii(x, aggregate_redaction=False))

# 保存结果
df.to_csv(output_path, index=False)
print("处理完成，输出已保存至:", output_path)
