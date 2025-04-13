from datasets import load_dataset
import pandas as pd

# 加载 Hugging Face 上的 Enron 数据集（train split）
dataset = load_dataset("snoop2head/enron_aeslc_emails", split="train")

# 取前 500 条样本
first_500 = dataset.select(range(500))

# 提取 'text' 字段并转为 DataFrame
df = pd.DataFrame(first_500['text'], columns=["text"])

# 保存为 Excel 文件
df.to_excel("enron-500.xlsx", index=False)
