import os
import pandas as pd
import numpy as np
from fuzzy_mark_2 import evaluate_llm_output_refined, normalize_and_split

def process_files(main_folder, gold_standard_path):
    strategies = []
    temperature_columns = []
    metrics = ['accuracy_ibd_type', 'accuracy_na', 'precision_na', 'recall_na', 'f1_score_na']
    results_data = {metric: [] for metric in metrics}
    std_data = {f'{metric}_std': [] for metric in metrics}

    gold_standard_df = pd.read_csv(gold_standard_path, delimiter='\t', header=0)

    for strategy_folder in os.listdir(main_folder):
        strategy_path = os.path.join(main_folder, strategy_folder)
        if os.path.isdir(strategy_path) and strategy_folder != '__pycache__':
            strategies.append(strategy_folder)
            strategy_results = {metric: {} for metric in metrics}
            strategy_stds = {metric: {} for metric in metrics}

            for temp_folder in os.listdir(strategy_path):
                temp_path = os.path.join(strategy_path, temp_folder)
                if os.path.isdir(temp_path) and temp_folder != '__pycache__':
                    temp_results = {metric: [] for metric in metrics}

                    for file in os.listdir(temp_path):
                        if file.endswith(('_1.csv', '_2.csv', '_3.csv')):
                            file_path = os.path.join(temp_path, file)
                            try:
                                llm_output_df = pd.read_csv(file_path, delimiter='\t', header=0)
                                results = evaluate_llm_output_refined(gold_standard_df, llm_output_df)
                                for metric in metrics:
                                    temp_results[metric].append(results[metric])
                            except Exception as e:
                                print(f"Error processing file {file_path}: {str(e)}")

                    for metric in metrics:
                        if temp_results[metric]:
                            avg_result = np.mean(temp_results[metric])
                            std_result = np.std(temp_results[metric])
                            strategy_results[metric][temp_folder] = avg_result
                            strategy_stds[metric][temp_folder] = std_result

                    if temp_folder not in temperature_columns:
                        temperature_columns.append(temp_folder)

            for metric in metrics:
                results_data[metric].append(strategy_results[metric])
                std_data[f'{metric}_std'].append(strategy_stds[metric])

    # Create DataFrames for results and standard deviations
    result_dfs = {}
    for metric in metrics:
        df = pd.DataFrame(results_data[metric], index=strategies, columns=temperature_columns)
        df.index.name = 'Strategy'
        result_dfs[metric] = df

        std_df = pd.DataFrame(std_data[f'{metric}_std'], index=strategies, columns=temperature_columns)
        std_df.index.name = 'Strategy'
        result_dfs[f'{metric}_std'] = std_df

    # Save results to CSV files
    for metric, df in result_dfs.items():
        df.to_csv(f'{metric}_results.csv')

    return result_dfs

# Example usage
main_folder = "" # Enter directory containing non-associations here
gold_standard_path = 'gold_standard.csv' # Gold standard used for assessing 104 abstracts, change accordingly for your own gold standard
results = process_files(main_folder, gold_standard_path)

# Print summary of results
for metric, df in results.items():
    print(f"\n{metric}:")
    print(df)