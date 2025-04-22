import pandas as pd
import subprocess
import time
import logging

# ------------------------------------------------------------------------------
# 1) Configuration
# ------------------------------------------------------------------------------
input_file = "enron.xlsx"          # Input Excel file
output_file = "all/reply_time_qwen7b.xlsx"  # Output Excel file

# Set up logging to a file. 
logging.basicConfig(
    filename='dataset/complex_log.txt', 
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Example prompt template
PROMPT_TEMPLATE = """You are a helpful email assistant. I have just received the following email. 
Please generate a reply for me. Only return the email body without reasoning.
Email:
{}
===================="""

model_list = [
    "qwen2.5:7b"
]

output_col_names = [
    "Reply_qwen2.5:7b"
]

# ------------------------------------------------------------------------------
# 2) Read the Excel file
# ------------------------------------------------------------------------------
df = pd.read_excel(input_file, dtype=str)
# df = pd.read_csv(input_file, dtype=str)

# Ensure the DataFrame has at least 1 column (the email body)
if df.shape[1] < 1:
    raise ValueError("The Excel file does not have at least one column for email text.")

# Create new columns for the model outputs if they do not exist
for col_name in output_col_names:
    if col_name not in df.columns:
        df[col_name] = ""

# Create a new column 'reply_time' for storing each row's processing time
if "reply_time" not in df.columns:
    df["reply_time"] = ""

# ------------------------------------------------------------------------------
# 3) Define a function to call local LLaMA models via ollama
# ------------------------------------------------------------------------------
def call_local_model(model_name: str, email_body: str, row_index: int) -> str:
    """
    Calls a local LLM model using `ollama run <model_name>` and returns its text response.
    Also logs input, output, and time taken.
    """
    prompt = PROMPT_TEMPLATE.format(email_body)

    # Log the input before calling the model
    logging.info(f"[Row {row_index}] Model: {model_name} | Input: {email_body}")

    start_time_model = time.time()
    process = subprocess.run(
        ["ollama", "run", model_name],
        input=prompt,
        text=True,
        capture_output=True
    )
    end_time_model = time.time()

    output_text = process.stdout.strip()

    # Log the output and time cost
    elapsed = end_time_model - start_time_model
    logging.info(f"[Row {row_index}] Model: {model_name} | Time: {elapsed:.2f}s | Output: {output_text}")

    return output_text

# ------------------------------------------------------------------------------
# 4) Process each row (skipping header), measure time and record processing time
# ------------------------------------------------------------------------------
start_time = time.time()
num_rows = len(df)

# 如果只想处理前 5 行（且第 1 行是表头），可将下面循环改为 range(1, min(num_rows, 6))。
for idx in range(1, num_rows):
    # 读取第一列的邮件内容
    email_text = df.iloc[idx, 0] if pd.notna(df.iloc[idx, 0]) else ""

    row_start_time = time.time()
    for m_idx, model_name in enumerate(model_list):
        # 调用模型获取回复，并存储结果
        response_text = call_local_model(model_name, email_text, idx)
        df.at[idx, output_col_names[m_idx]] = response_text
    row_end_time = time.time()

    # 计算并记录该行处理的时间
    elapsed_row_time = row_end_time - row_start_time
    df.at[idx, "reply_time"] = elapsed_row_time

    print(f"Processed row {idx}/{num_rows - 1} in {elapsed_row_time:.2f} seconds.")

    # === 新增：每处理 10 行就将结果写入一次 Excel，以防中途意外导致数据丢失 ===
    if idx % 10 == 0:
        df.to_excel(output_file, index=False)
        print(f"Temporary save: wrote partial results to {output_file} (after row {idx}).")

end_time = time.time()
total_time = end_time - start_time
avg_time_per_row = total_time / (num_rows - 1) if num_rows > 1 else 0

# ------------------------------------------------------------------------------
# 5) 最后一次完整保存，并打印摘要
# ------------------------------------------------------------------------------
df.to_excel(output_file, index=False)

# Print summary
print(f"\nProcessing completed (first {num_rows-1} rows).")
print(f"Total execution time: {total_time:.2f} seconds.")
print(f"Average time per row: {avg_time_per_row:.2f} seconds.")
print(f"The updated file is saved to: {output_file}")
print("Logs have been recorded in dataset/complex_log.txt.")
