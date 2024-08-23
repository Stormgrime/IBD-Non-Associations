# fuzzy_mark_2.py
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
import re

def normalize_and_split(text, delimiter=';'):
    if pd.isna(text) or text.lower() in ['none', 'n/a']:
        return []
    text = str(text).lower()
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s;]', '', text)
    return [item.strip() for item in text.split(delimiter) if item.strip()]

def calculate_similarity(list1, list2):
    if not list1 and not list2:
        return 1.0
    if not list1 or not list2:
        return 0.0

    similarities = []
    for item1 in list1:
        max_similarity = max(fuzz.ratio(item1, item2) / 100 for item2 in list2)
        similarities.append(max_similarity)

    return sum(similarities) / len(list1)

def evaluate_llm_output_refined(gold_standard_df, llm_output_df):
    # Normalize and split IBD types and non-associations
    for df in [gold_standard_df, llm_output_df]:
        df['ibd_types'] = df.iloc[:, 1].apply(normalize_and_split)
        df['non_assoc'] = df.iloc[:, 2].apply(normalize_and_split)

    # Calculate similarities for IBD types
    similarities_ibd = [calculate_similarity(gold, llm)
                        for gold, llm in zip(gold_standard_df['ibd_types'], llm_output_df['ibd_types'])]

    # Calculate confusion matrix for non-associations
    tp_na = fp_na = tn_na = fn_na = 0

    for gold, llm in zip(gold_standard_df['non_assoc'], llm_output_df['non_assoc']):
        if not gold and not llm:
            tn_na += 1
        elif gold and llm:
            tp_na += min(len(gold), len(llm))  # Count matches
            fp_na += max(len(llm) - len(gold), 0)  # Extra predictions
            fn_na += max(len(gold) - len(llm), 0)  # Missed predictions
        elif gold:
            fn_na += len(gold)
        elif llm:
            fp_na += len(llm)

    # Calculate metrics
    accuracy_ibd_type = np.mean(similarities_ibd)
    total_na = tp_na + fp_na + tn_na + fn_na
    accuracy_na = (tp_na + tn_na) / total_na if total_na > 0 else 0
    precision_na = tp_na / (tp_na + fp_na) if (tp_na + fp_na) > 0 else 0
    recall_na = tp_na / (tp_na + fn_na) if (tp_na + fn_na) > 0 else 0
    f1_score_na = 2 * (precision_na * recall_na) / (precision_na + recall_na) if (precision_na + recall_na) > 0 else 0

    return {
        "accuracy_ibd_type": accuracy_ibd_type,
        "accuracy_na": accuracy_na,
        "precision_na": precision_na,
        "recall_na": recall_na,
        "f1_score_na": f1_score_na,
        "true_positives_na": int(tp_na),
        "false_positives_na": int(fp_na),
        "true_negatives_na": int(tn_na),
        "false_negatives_na": int(fn_na)
    }

# This script is to be used as an import for results calculation