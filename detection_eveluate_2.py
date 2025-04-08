import pandas as pd
import json
import numpy as np

# ---------------------------
# 1. 读取数据
# ---------------------------
input_file = "enron/enron_private_output.xlsx"
df = pd.read_excel(input_file)

# ---------------------------
# 2. 定义待评估的列
# ---------------------------
# Ground Truth 列，这里假定它存储的是一个 JSON 字符串列表，比如 '["Tuesday", "11:45"]'
ground_truth_col = "Ground Truth"

# 模型预测结果列
model_cols = [
    "Extracted_gemma3:1b",
    "Extracted_gemma:2b",
    "Extracted_llama3.2:3b",
    "Extracted_mistral",
    "Extracted_GPT4"
]

# ---------------------------
# 3. 工具函数
# ---------------------------
def parse_values(value):
    """将 JSON 格式的字符串转换为列表；若为空则返回空列表"""
    if pd.isnull(value) or value == "None":
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return []

def compute_metrics(gt_list, pred_list):
    """
    输入为 ground truth 列表和预测列表（都作为字符串列表格式）
    输出 precision, recall, F1 三个指标
    """
    # 将列表转为集合，方便计算 (假定元素唯一)
    set_gt = set(gt_list)
    set_pred = set(pred_list)
    
    # 情况 1：如果 ground truth 是空
    if len(set_gt) == 0:
        if len(set_pred) == 0:
            return 1.0, 1.0, 1.0  # 理想状态
        else:
            return 0.0, 0.0, 0.0  # 误报
    
    # 计算 True Positives, False Positives, False Negatives
    TP = len(set_gt & set_pred)
    FP = len(set_pred - set_gt)
    FN = len(set_gt - set_pred)
    
    # 计算 precision 和 recall，注意防止除0
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    recall    = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1

# ---------------------------
# 4. 计算每个模型在每条邮件上的精确率、召回率和 F1得分，并累加结果
# ---------------------------
# 准备一个字典，记录每个模型的累计分数和计数
scores = {model: {"precision": 0.0, "recall": 0.0, "f1": 0.0, 
                  "micro_TP": 0, "micro_FP": 0, "micro_FN": 0} 
          for model in model_cols}

num_emails = len(df)

# 逐行处理邮件
for index, row in df.iterrows():
    gt_values = parse_values(row[ground_truth_col])
    
    for model in model_cols:
        pred_values = parse_values(row[model])
        
        # 计算 per-email 指标
        precision, recall, f1 = compute_metrics(gt_values, pred_values)
        
        # 对于 macro average，将每封邮件的指标累加
        scores[model]["precision"] += precision
        scores[model]["recall"]    += recall
        scores[model]["f1"]        += f1
        
        # 同时计算 micro 指标（累加 TP, FP, FN）
        set_gt   = set(gt_values)
        set_pred = set(pred_values)
        # 对空 ground truth 的情况，如果 ground truth 为空，且预测为空已经给1分，
        # 但如果预测不为空，我们认为所有预测都为 FP（无 TP，因为没有应该识别的）
        if len(set_gt) == 0:
            if len(set_pred) > 0:
                scores[model]["micro_FP"] += len(set_pred)
            # 若为空，不改变 micro_TP 或 micro_FN
        else:
            TP = len(set_gt & set_pred)
            FP = len(set_pred - set_gt)
            FN = len(set_gt - set_pred)
            scores[model]["micro_TP"] += TP
            scores[model]["micro_FP"] += FP
            scores[model]["micro_FN"] += FN

# ---------------------------
# 5. 计算各模型的 macro average 和 micro average
# ---------------------------
results_list = []
for model in model_cols:
    macro_precision = scores[model]["precision"] / num_emails
    macro_recall    = scores[model]["recall"] / num_emails
    macro_f1        = scores[model]["f1"] / num_emails
    
    # 计算 micro average
    TP_total = scores[model]["micro_TP"]
    FP_total = scores[model]["micro_FP"]
    FN_total = scores[model]["micro_FN"]
    micro_precision = TP_total / (TP_total + FP_total) if (TP_total + FP_total) > 0 else 0.0
    micro_recall    = TP_total / (TP_total + FN_total) if (TP_total + FN_total) > 0 else 0.0
    micro_f1        = (2 * micro_precision * micro_recall / (micro_precision + micro_recall)
                       if (micro_precision + micro_recall) > 0 else 0.0)
    
    results_list.append({
        "Model": model,
        "Macro Precision": macro_precision,
        "Macro Recall": macro_recall,
        "Macro F1": macro_f1,
        "Micro Precision": micro_precision,
        "Micro Recall": micro_recall,
        "Micro F1": micro_f1
    })

results_df = pd.DataFrame(results_list)

# ---------------------------
# 6. 保存评估结果
# ---------------------------
results_output_file = "enron/evaluation_results_precision.xlsx"
results_df.to_excel(results_output_file, index=False)

print("Evaluation with precision, recall and F1 completed.")
print(results_df)
