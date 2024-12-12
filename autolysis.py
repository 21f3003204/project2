import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import openai

# Set up OpenAI API key
openai.api_key = os.environ["AIPROXY_TOKEN"]

def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        print("Dataset loaded successfully!")
        return df
    except Exception as e:
        print(f"Error loading dataset: {e}")
        exit(1)

def analyze_data(df):
    summary = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "missing_values": df.isnull().sum().to_dict(),
        "summary_statistics": df.describe(include='all').to_dict(),
    }
    return summary

def generate_visualizations(df, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Example: Correlation heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(df.corr(), annot=True, cmap="coolwarm")
    heatmap_path = os.path.join(output_dir, "correlation_heatmap.png")
    plt.savefig(heatmap_path)
    plt.close()
    return [heatmap_path]

def ask_llm_for_story(data_summary, visual_paths):
    prompt = f"""
    Here's the summary of the dataset:
    {data_summary}
    
    The following visualizations were generated:
    {visual_paths}

    Write a story summarizing the dataset, the key findings, and actionable insights.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        exit(1)
    
    dataset_path = sys.argv[1]
    output_dir = os.path.dirname(dataset_path)
    
    # Load and analyze data
    df = load_data(dataset_path)
    summary = analyze_data(df)
    
    # Generate visualizations
    visual_paths = generate_visualizations(df, output_dir)
    
    # Use LLM for storytelling
    story = ask_llm_for_story(summary, visual_paths)
    
    # Save story to README.md
    with open(os.path.join(output_dir, "README.md"), "w") as f:
        f.write(story)
    
    print("Analysis complete. Results saved to README.md and PNG files.")

if __name__ == "__main__":
    main()

