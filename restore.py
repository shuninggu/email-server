import re
import json
import pandas as pd

def restore_reply(
    input_excel_path="all/with_reply.xlsx",
    output_excel_path="all/reply_restored.xlsx"
):
    # 1. 读取 Excel
    print("读取文件:", input_excel_path)
    df = pd.read_excel(input_excel_path)

    # 确保存在所需列
    col_reply_mask = "reply_masked"
    col_privacy_json = "storage_privacy.json"
    col_restored = "restored_value"  # 新增列

    if col_reply_mask not in df.columns or col_privacy_json not in df.columns:
        raise ValueError(f"Excel中缺少 {col_reply_mask} 或 {col_privacy_json} 列。")

    # 用于匹配 reply_mask 中的 [xxxx]
    # 注意：如果占位符中可能存在更复杂的字符，需要适当调整
    pattern_placeholder = re.compile(r"\[[^\]]+\]")

    total_rows = len(df)
    print(f"共 {total_rows} 行，开始处理占位符替换...")

    for idx in range(total_rows):
        # 每隔50行打印一下进度（可根据需要调整）
        if idx % 50 == 0:
            print(f"正在处理第 {idx+1} / {total_rows} 行...")

        reply_text = str(df.at[idx, col_reply_mask])  # reply_mask 的文本
        privacy_str = str(df.at[idx, col_privacy_json])  # storage_privacy.json 的字符串

        # 如果这行的 storage_privacy.json 为 "None"，则无需替换
        if privacy_str == "None":
            # 直接把 reply_mask 原样放到 restored_value
            df.at[idx, col_restored] = reply_text
            continue

        # 尝试将该列解析为 JSON 数组
        try:
            records = json.loads(privacy_str)
        except json.JSONDecodeError:
            # 解析失败，可能是格式问题；可根据实际需求做其他处理
            df.at[idx, col_restored] = reply_text
            continue

        # 在 reply_text 中查找所有占位符
        placeholders = pattern_placeholder.findall(reply_text)
        # placeholders 可能重复出现，如 ["[name_1]", "[name_1]", "[school_2]", ...]

        # 按出现顺序依次替换
        for ph in placeholders:
            # 在当前记录数组中查找 replacedValue == ph 的项
            # 可能不止一个，但一般而言只会有一个匹配
            match_item = next((item for item in records if item.get("replacedValue") == ph), None)
            if match_item:
                original_val = match_item.get("originalValue", "")
                # 将 reply_text 中的该占位符替换为 originalValue
                reply_text = reply_text.replace(ph, original_val)

        # 将最终替换完的结果写入
        df.at[idx, col_restored] = reply_text

    # 2. 写出新的 Excel
    print("全部处理完成，写出结果到:", output_excel_path)
    df.to_excel(output_excel_path, index=False)
    print("处理结束。")


if __name__ == "__main__":
    restore_reply()
