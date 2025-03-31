import pandas as pd
import subprocess
import time

# ------------------------------------------------------------------------------
# 1) Configuration
# ------------------------------------------------------------------------------
# Input and output files
input_file = "enron_labeled.xlsx"
output_file = "enron_gemma3_1b.xlsx"

# Prompt template
# PROMPT_TEMPLATE = """
# Any privacy sensitive data in the following email body? 
# Please return all potential private data in a json format: ["private data1", "private data2", ...]. 
# Return only one json, no comment, no explanation. 
# If there are repeated values, display them only once.

# ======== email body ========
# {}.
# """

# PROMPT_TEMPLATE = """
# Identify privacy-sensitive data such as names, emails, phone numbers, addresses, IDs, financial data, or personally identifiable information in the email text below.

# List each detected item exactly as it appears in the text, one per line, without numbering, extra text, or explanation.  
# If none found, return "NONE".

# Email Body:
# {}

# List:

# """

PROMPT_TEMPLATE = """
List ALL privacy-sensitive data EXACTLY as they appear in the text below.
Do NOT add anything that is not explicitly written in the email body.
One item per line, no numbering, no explanation, nothing else.
If none, write NONE.

Email Body:
{}

List:
"""

# ------------------------------------------------------------------------------
# 2) Read the Excel file
# ------------------------------------------------------------------------------
df = pd.read_excel(input_file, dtype=str)

num_rows = len(df)  # Number of rows

# 如果表格列数不足 4 列，就在第 4 列插入一个新列 "Prediction"
if df.shape[1] < 4:
    df.insert(3, "Prediction", "")

# ------------------------------------------------------------------------------
# 3) Define a function to call the local LLaMA model
# ------------------------------------------------------------------------------
def call_llama_local(email_body: str) -> str:
    """
    Calls the local LLaMA model via `ollama run gemma3:1b` and returns the model output.
    """
    prompt = PROMPT_TEMPLATE.format(email_body)

    process = subprocess.run(
        ["ollama", "run", "gemma3:1b"],
        input=prompt,
        text=True,
        capture_output=True
    )

    return process.stdout.strip()

# ------------------------------------------------------------------------------
# 4) Process rows and measure execution time
# ------------------------------------------------------------------------------
start_time = time.time()  # Start time

# 跳过第一行表头，从第二行开始处理
# for idx in range(1, num_rows):
for idx in range(1, min(11, num_rows)):
    email_text = df.iloc[idx, 0] if pd.notna(df.iloc[idx, 0]) else ""

    row_start_time = time.time()
    model_response = call_llama_local(email_text)
    row_end_time = time.time()

    # 将结果写入第 4 列（列索引为 3）
    df.iloc[idx, 3] = model_response

    print(f"Processed row {idx}/{num_rows-1} in {row_end_time - row_start_time:.2f} seconds.")

end_time = time.time()
total_time = end_time - start_time
avg_time_per_row = total_time / (num_rows - 1) if num_rows > 1 else 0

# ------------------------------------------------------------------------------
# 5) Save the updated DataFrame to a new XLSX file
# ------------------------------------------------------------------------------
df.to_excel(output_file, index=False)

# Print summary statistics
print(f"\nProcessing completed (first {num_rows-1} rows only).")
print(f"Total execution time: {total_time:.2f} seconds.")
print(f"Average time per row: {avg_time_per_row:.2f} seconds.")
print(f"The updated file is saved to: {output_file}")
