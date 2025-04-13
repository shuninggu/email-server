import os
import json
import time
import openai
import pandas as pd

# Set your API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("Please set your OPENAI_API_KEY environment variable.")

def detect_private_values(email_text):
    """
    Use GPT-4 to extract private values from an email text.
    The response should be a JSON list (e.g. ["Randy", "Patti S", "Phillip"]).
    """
    prompt = (
        "Extract any private values from the following email text. "
        "Private values include names, email addresses, phone numbers, or any sensitive identifiers. "
        "Return the extracted values in a JSON list. "
        "If no private values are found, return an empty JSON list ([]).\n\n"
        f"Email text:\n{email_text}"
    )
    
    # Call the GPT-4 chat completion API
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that extracts private values from email text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=150
        )
    except Exception as e:
        print("Error using ChatCompletion:", e)
        raise e

    # Extract GPT-4's answer and try to load it as JSON.
    message = response["choices"][0]["message"]["content"].strip()
    try:
        private_values = json.loads(message)
    except json.JSONDecodeError:
        # If the output is not valid JSON, simply return the raw message.
        private_values = message

    return json.dumps(private_values)

# Load your dataset (it assumes the first column contains email text).
df = pd.read_excel("enron.xlsx")

detected_results = []
# Process only the first 20 rows
for idx, row in df.head(20).iterrows():
    email_text = row[df.columns[0]]
    print(f"Processing row {idx}: {email_text[:50]}...")
    detected = detect_private_values(email_text)
    detected_results.append(detected)
    time.sleep(1)  # small delay to avoid rate limits

# Create a new column and assign results for only the first 20 rows.
df.loc[df.index[:20], "Detected Private Values"] = detected_results

# Save the updated DataFrame to a new Excel file.
output_file = "enron_with_detected_first20.xlsx"
df.to_excel(output_file, index=False)
print(f"Detection completed for the first 20 rows. Results are saved in {output_file}.")
