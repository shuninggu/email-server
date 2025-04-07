    # """download top 100 emails from the Enron dataset and save them as a CSV file.
    # """

# from datasets import load_dataset
# import pandas as pd

# # 加载 Hugging Face 上的 Enron 数据集
# dataset = load_dataset("LLM-PBE/enron-email", split="train")

# # 获取前 100 条数据
# first_100 = dataset.select(range(100))

# # 转换为 pandas 表格格式
# df = pd.DataFrame(first_100)

# # 显示表格（或保存为文件）
# print(df.head())  # 打印前几行
# df.to_csv("pbe_top100.csv", index=False)  # 可选：保存为 CSV 文件

from datasets import load_dataset
import pandas as pd

# 加载完整的 Enron 邮件数据集
dataset = load_dataset("LLM-PBE/enron-email", split="train")

# 转换为 pandas DataFrame
df = pd.DataFrame(dataset)

# 可选：显示前几行确认加载成功
print(df.head())

# 可选：保存为 CSV 文件
df.to_csv("pbe/pbe_full.csv", index=False)
