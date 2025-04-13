from datasets import load_dataset
import pandas as pd

# 加载 Hugging Face 上的 Enron 数据集（train split）
dataset = load_dataset("snoop2head/enron_aeslc_emails", split="train")

# 只取前 500 条
first_500 = dataset.select(range(500))

def extract_body(text):
    # 按 'Body:' 分割，仅保留第一次出现的 Body: 后面部分
    parts = text.split("Body:", 1)
    # 如果找到了 'Body:'，则返回它后面的内容，否则返回原文本
    if len(parts) > 1:
        return parts[1].strip()
    return text.strip()

# 将每条数据的 text 字段取出，并进行清洗
cleaned_texts = [extract_body(item["text"]) for item in first_500]

# 转为 DataFrame
df = pd.DataFrame(cleaned_texts, columns=["text"])

# 保存为 Excel 文件
df.to_excel("enron-500-body.xlsx", index=False)
