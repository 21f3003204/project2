import os
import sys
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import httpx
from IPython.display import Image, display

# Constants
AIPROXY_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise ValueError("AIPROXY_TOKEN environment variable is not set")

def load_data(file_path):
    """Load CSV file into a pandas DataFrame."""
    print(f"Loading data from {file_path}...")
    df = pd.read_csv(file_path, encoding='ISO-8859-1')
    print(f"Data loaded successfully. Shape: {df.shape}")
    return df

def basic_analysis(df):
    """Perform basic analysis on the DataFrame."""
    print("Performing basic analysis...")
    analysis = {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "summary_stats": df.describe().to_dict(),
    }
    print("Basic analysis completed.")
    return analysis

def call_llm(prompt, function_call=None):
    """Call the LLM via AI Proxy."""
    print("Calling LLM via AI Proxy...")
    headers = {
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
    }
    if function_call:
        payload["functions"] = [function_call]
        payload["function_call"] = "auto"

    try:
        response = httpx.post(AIPROXY_URL, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Raw API Response: {response.text}")

        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return None

        response_data = response.json()
        if 'choices' not in response_data:
            print("Error: Unexpected API response structure")
            print("Full response:", response_data)
            return None

        print("LLM call successful.")
        return response_data
    except httpx.RequestError as e:
        print(f"An error occurred while requesting: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print("Raw response:", response.text)
        return None

def create_visualization(df, viz_type, columns):
    """Create a visualization based on the specified type and columns."""
    print(f"Creating {viz_type} visualization for columns: {columns}")

    # Ensure the visualization folder exists
    visualization_folder = "C:\\Users\\Mrinmayee\\OneDrive\\Desktop\\project2\\visualization"
    os.makedirs(visualization_folder, exist_ok=True)

    plt.figure(figsize=(10, 6))
    if viz_type == "heatmap":
        sns.heatmap(df[columns].corr(), annot=True, cmap="coolwarm")
        plt.title("Correlation Heatmap")
    elif viz_type == "scatter":
        sns.scatterplot(data=df, x=columns[0], y=columns[1])
        plt.title(f"Scatter plot: {columns[0]} vs {columns[1]}")
    elif viz_type == "histogram":
        sns.histplot(data=df, x=columns[0], kde=True)
        plt.title(f"Histogram of {columns[0]}")

    plt.tight_layout()
    file_name = f"{viz_type}_plot.png"
    full_path = os.path.join(visualization_folder, file_name)
    plt.savefig(full_path)
    plt.close()
    print(f"Visualization saved as {full_path}")

def generate_narrative(analysis_results, visualizations):
    """Generate a narrative using the LLM based on analysis results and visualizations."""
    print("Generating narrative...")
    prompt = f"""
    Based on the following analysis results and visualizations, write a comprehensive story about the dataset:

    Analysis Results:
    {json.dumps(analysis_results, indent=2)}

    Visualizations Created:
    {', '.join(visualizations)}

    Please structure the story with the following sections:
    1. Brief description of the data
    2. Analysis performed
    3. Key insights discovered
    4. Implications of the findings

    Format the response in Markdown, including appropriate headers and emphasis.
    """
    response = call_llm(prompt)
    if response and 'choices' in response:
        narrative = response['choices'][0]['message']['content']
        print("Narrative generated successfully.")
        return narrative
    else:
        print("Error: Failed to generate narrative.")
        return "Error: Unable to generate narrative due to API issues."

def main(file_path):
    print(f"Starting analysis for file: {file_path}")

    # Load data
    df = load_data(file_path)

    # Perform basic analysis
    analysis_results = basic_analysis(df)

    # Use LLM for advanced analysis suggestions
    print("Requesting advanced analysis suggestions from LLM...")
    analysis_prompt = f"""
    Given the following basic analysis of a dataset:
    {json.dumps(analysis_results, indent=2)}

    Suggest 3 advanced analyses that could provide deeper insights into this data.
    For each analysis, provide:
    1. A brief description of the analysis
    2. The Python code to perform the analysis
    3. A suitable visualization type for the results
    """
    advanced_analysis_suggestions = call_llm(analysis_prompt)

    if advanced_analysis_suggestions is None:
        print("Error: Failed to get valid response from AI Proxy for advanced analysis suggestions.")
        return

    # Perform advanced analyses and create visualizations
    # Perform advanced analyses and create visualizations
    visualizations = []
    print("Performing advanced analyses and creating visualizations...")
    for i, suggestion in enumerate(advanced_analysis_suggestions['choices'][0]['message']['content'].split('\n\n')):
        print(f"Processing suggestion {i+1}...")
        if 'Python code:' in suggestion and 'visualization type:' in suggestion:
            try:
                # Extract and execute the Python code
                code = suggestion.split('Python code:')[1].split('visualization type:')[0].strip()
                print(f"Executing code:\n{code}")
                exec(code)
                print("Code executed successfully.")

                # Extract visualization type
                viz_type = suggestion.split('visualization type:')[1].strip().lower()
                if viz_type in ['heatmap', 'scatter', 'histogram']:
                    columns = df.select_dtypes(include=['number']).columns[:2].tolist()
                    create_visualization(df, viz_type, columns)
                    visualizations.append(f"visualization/{viz_type}_plot.png")
            except Exception as e:
                print(f"Error processing suggestion {i+1}: {e}")
                continue
        else:
            print(f"Suggestion {i+1} skipped due to missing 'Python code' or 'visualization type'.")


    # Generate narrative
    narrative = generate_narrative(analysis_results, visualizations)

    # Save narrative to README.md
    print("Saving narrative to README.md...")
    with open("README.md", "w") as f:
        f.write(narrative)

    print("Analysis complete. Results saved in README.md and visualization PNG files.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <csv_file_path>")
        sys.exit(1)
    main(sys.argv[1])
