import pandas as pd
import time
from openai import OpenAI
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

input_file = "enron.xlsx"          # Input Excel file
output_file = "enron/enron_output.xlsx"  # Output Excel file

PROMPT_TEMPLATE = """You are a helpful email assistant. I have just received the following email.
Please generate a reply for me. Only return the email body without reasoning.
Email:
{}
===================="""

# model_gpt3_5 = "gpt-3.5-turbo"
model_gpt4 = "gpt-4o"

# col_reply_gpt3_5 = "Reply_gpt3.5"
col_reply_gpt4 = "Reply_gpt4o"

# ------------------------------------------------------------------------------
# 3) Read the Excel file
# ------------------------------------------------------------------------------
df = pd.read_excel(input_file, dtype=str)
# df = pd.read_csv(input_file, dtype=str)

# if col_reply_gpt3_5 not in df.columns:
#     df[col_reply_gpt3_5] = ""

if col_reply_gpt4 not in df.columns:
    df[col_reply_gpt4] = ""

# ------------------------------------------------------------------------------
# 4) Call GPT models via OpenAI SDK v1.x
# ------------------------------------------------------------------------------
def call_openai_chat(model_name: str, content: str) -> str:
    """
    Calls the OpenAI Chat API using new v1.x client interface.
    """
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are ChatGPT."},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI model {model_name}: {e}")
        return ""

# ------------------------------------------------------------------------------
# 5) Process each row
# ------------------------------------------------------------------------------
start_time = time.time()
num_rows = len(df)

# Use this if you only want to process the first 5 rows (excluding header):
# for idx in range(1, min(num_rows, 6)):
for idx in range(1, num_rows):
    email_text = df.iloc[idx, 0]
    if not isinstance(email_text, str):
        email_text = ""

    prompt_text = PROMPT_TEMPLATE.format(email_text)
    row_start_time = time.time()

    # GPT-3.5
    # gpt3_5_reply = call_openai_chat(model_gpt3_5, prompt_text)
    # df.at[idx, col_reply_gpt3_5] = gpt3_5_reply

    # GPT-4
    gpt4_reply = call_openai_chat(model_gpt4, prompt_text)
    df.at[idx, col_reply_gpt4] = gpt4_reply

    row_end_time = time.time()
    print(f"Processed row {idx}/{num_rows - 1} in {row_end_time - row_start_time:.2f} seconds.")

# ------------------------------------------------------------------------------
# 6) Save to Excel
# ------------------------------------------------------------------------------
df.to_excel(output_file, index=False)

end_time = time.time()
print(f"\nFinished processing {num_rows - 1} rows.")
print(f"Total time: {end_time - start_time:.2f} seconds.")
print(f"Output saved to {output_file}")
