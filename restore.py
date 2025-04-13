import re
import json
import pandas as pd

def process_restore_excel(
    input_excel_path: str = "all/restore.xlsx",
    output_excel_path: str = "all/restore_processed.xlsx",
    output_json_path: str = "all/storage_privacy.json"
):
    print("开始处理Excel:", input_excel_path)
    df = pd.read_excel(input_excel_path)

    col_body = "Body"
    col_private_llm = "Private_llama3.2:3b"
    col_json = "storage_privacy.json"
    col_result = "result"

    if col_body not in df.columns or col_private_llm not in df.columns:
        raise ValueError("Excel文件中缺少所需的列(body或Private_llama3.2:3b)")

    # 正则模式：匹配 "key" : "value"
    pattern = re.compile(r'"\s*([^"]+)\s*"\s*:\s*"([^"]+)"')

    global_pairs = []

    total_rows = len(df)
    print(f"共读取到 {total_rows} 行数据，即将开始处理...")

    for row_idx in range(total_rows):
        if row_idx % 50 == 0:
            print(f">> 正在处理第 {row_idx + 1} 行 / 共 {total_rows} 行...")

        original_text = str(df.at[row_idx, col_body])   # A
        processed_text = str(df.at[row_idx, col_private_llm])  # B

        # 在B中查找所有的 key-value 对
        matches = pattern.findall(processed_text)
        seen_values = set()

        row_pairs = []
        pair_id = 1

        # 针对每个匹配进行处理
        for key_str, value_str in matches:
            if value_str not in seen_values:
                seen_values.add(value_str)
                record = {
                    "id": pair_id,
                    "key": key_str.strip(),
                    "originalValue": value_str,
                    "replacedValue": f"[{key_str.strip()}_{pair_id}]"
                }
                row_pairs.append(record)
                pair_id += 1

        # 在 original_text 中逐个替换
        result_text = original_text
        for pair in row_pairs:
            # 如果想要更加详细的log，比如每次替换什么，可以在这里print出来
            # print(f"  - 替换: {pair['originalValue']} -> {pair['replacedValue']}")
            result_text = result_text.replace(pair["originalValue"], pair["replacedValue"])

        # 写入 dataFrame
        if len(row_pairs) == 0:
            df.at[row_idx, col_json] = "None"
        else:
            df.at[row_idx, col_json] = json.dumps(row_pairs, ensure_ascii=False)

        df.at[row_idx, col_result] = result_text

        # 将本行结果追加到全局列表
        for pair in row_pairs:
            global_pairs.append({
                "rowIndex": row_idx,
                "id": pair["id"],
                "key": pair["key"],
                "originalValue": pair["originalValue"],
                "replacedValue": pair["replacedValue"]
            })

    print("所有行处理完毕，正在写出全局 JSON 文件:", output_json_path)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(global_pairs, f, ensure_ascii=False, indent=2)

    print("正在写出处理结果到新的Excel文件:", output_excel_path)
    df.to_excel(output_excel_path, index=False)
    print("处理完成！")


if __name__ == "__main__":
    process_restore_excel()
