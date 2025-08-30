import streamlit as st
from utils.llm_helpers import Summarizer
from utils.analysis_feature import CostAnalyzer, TextAnalyzer, ModelBenchmark

# Add a sidebar navigation
PAGES = {
    "Analyze Text": "analyze",
    "Documentation": "docs"
}

def show_documentation():
    st.title("Project Documentation")
    st.markdown("""
    # Text Analysis Tool

    A powerful web application for text analysis, summarization, and cost estimation using various language models.

    ## Author
    Haroon Ahmad @Buildables

    ## Features

    ###  Text Summarization
    - Supports multiple AI models (Gemini 2.5 Pro, GPT-5)
    - Generates concise summaries of input text
    - Real-time processing with progress indication

    ###  Cost Estimation
    - Calculates estimated costs for API usage
    - Supports multiple pricing models
    - Displays breakdown of input/output token costs

    ###  Token Analysis
    - Detailed tokenization using different models (GPT-2, BERT)
    - Token frequency analysis
    - Visual token distribution

    ###  Performance Benchmarking
    - Measures processing latency
    - Calculates tokens/second metrics
    - Compares performance across different models

    ## Prerequisites
    - Python 3.8+
    - Required API keys:
      - Google Gemini API key
      - OpenAI API key

    ## Installation
    ```bash
    pip install -r requirements.txt
    ```
    Create a `.env` file with your API keys.
    """)

st.set_page_config(page_title="Text Analysis Tool", layout="wide")

st.title("📄 Text Analysis & Cost Estimator")

# Sidebar navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

# Only show model settings in the analyze page
if PAGES[selection] == "analyze":
    st.sidebar.header("Model & Settings")
    summarizer_model = st.sidebar.selectbox(
        "Summarizer Model",
        ["gemini-2.5-pro", "gpt-5"]
    )
    tokenizer_model = st.sidebar.selectbox(
        "Tokenizer Model",
        ["gpt2", "bert-base-uncased"]
    )

# Show the selected page
if PAGES[selection] == "analyze":
    # Text input area
    input_text = st.text_area("Enter your text here:", height=250)


    if st.button("Analyze"):
        if not input_text.strip():
            st.warning("Please enter some text for analysis.")
        else:
            # Initialize benchmark
            benchmark = ModelBenchmark(summarizer_model)
            
            # Start timing before summarization
            benchmark.start_timer()
            
            st.subheader(" Summarizing...")
            summarizer = Summarizer(summarizer_model)
            output_text = summarizer.summarize(input_text)
            st.text_area("Summary:", value=output_text, height=150)

            st.subheader(" Cost Estimating...")
            analyzer = CostAnalyzer(summarizer_model)
            cost_result = analyzer.analyze_text_and_cost(input_text, output_text)
            st.json(cost_result)

            st.subheader(" Token Analyzing...")
            tokenizer = TextAnalyzer(tokenizer_model)
            analysis_result = tokenizer.analyze(input_text)
            st.write(f"Model: {analysis_result['model_name']}")
            st.write(f"Total Tokens: {analysis_result['token_count']}")
            st.write("Tokens:")
            st.text(" | ".join(analysis_result['tokens']))
            
            # Record tokens and stop timing after all operations
            benchmark.record_token_counts(input_text, output_text)
            benchmark.stop_timer()
            
            # Display benchmark results
            st.subheader("⏱ Performance Benchmark")
            
            metrics = benchmark.get_metrics()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Latency", f"{metrics['total_time_seconds']:.2f}s")
            with col2:
                st.metric("Input Tokens/s", f"{metrics['tokens_per_second']:.1f}")
            with col3:
                st.metric("Output Tokens/s", f"{metrics['output_tokens_per_second']:.1f}")
                
            st.caption("Note: Benchmark includes summarization time and token counting")

# Show documentation page
elif PAGES[selection] == "docs":
    show_documentation()
