import os
from utils.llm_helpers import Summarizer
from utils.analysis_feature import CostAnalyzer, TextAnalyzer, ModelBenchmark


def load_input_texts():
    """
    Loads all input text files from the data folder.
    Returns a dictionary with filename -> file contents.
    """
    BASE_DIR = os.path.dirname(__file__)  # directory of main.py
    DATA_DIR = os.path.join(BASE_DIR, "data")

    files = [
        os.path.join(DATA_DIR, "academic_abstract.txt"),
        os.path.join(DATA_DIR, "news_article.txt"),
        os.path.join(DATA_DIR, "reddit_post.txt"),
    ]

    texts = {}
    for file_path in files:
        file_name = os.path.basename(file_path)  # just the filename
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                texts[file_name] = f.read()
        except FileNotFoundError:
            print(f"File not found: {file_name}")

    return texts


def run_benchmarks(input_text: str):
    """Run performance benchmarks on different models."""
    from utils.llm_helpers import Summarizer
    
    print("\n" + "="*60)
    print("RUNNING PERFORMANCE BENCHMARKS")
    print("="*60)
    
    models = ["gpt-5", "gemini-2.5-pro"]
    benchmarks = []
    
    for model_name in models:
        try:
            print(f"\nBenchmarking {model_name}...")
            benchmark = ModelBenchmark(model_name)
            summarizer = Summarizer(model_name)
            
            # Start timing
            benchmark.start_timer()
            
            # Generate summary
            output_text = summarizer.summarize(input_text)
            
            # Stop timing and record metrics
            benchmark.stop_timer()
            benchmark.record_token_counts(input_text, output_text)
            
            # Get and store metrics
            metrics = benchmark.get_metrics()
            benchmarks.append(metrics)
            
            # Print individual model results
            print(f"  • Completed in {metrics['total_time_seconds']:.2f} seconds")
            print(f"  • Speed: {metrics['tokens_per_second']:.2f} tokens/second")
            
        except Exception as e:
            print(f"  • Error benchmarking {model_name}: {str(e)}")
    
    # Print comparison of all benchmarks
    if benchmarks:
        print(ModelBenchmark.compare_benchmarks(benchmarks))


if __name__ == "__main__":
    # Load all input texts
    texts = load_input_texts()

    for name, input_text in texts.items():
        print(f"\n\n Running analysis for: {name}")
        print("=" * 60)

        # Cost Estimation for Gemini
        gemini_summarizer = Summarizer("gemini-2.5-pro")
        output_text = gemini_summarizer.summarize(input_text)
        analyzer = CostAnalyzer("gemini-2.5-pro")
        result = analyzer.analyze_text_and_cost(input_text, output_text)

        print("\nCost Estimation for Gemini:" + "\n" + "-" * 50)
        for key, value in result.items():
            print(f"{key}: {value}")

        # Cost Estimation for OpenAI
        gpt_summarizer = Summarizer("gpt-5")
        output_text = gpt_summarizer.summarize(input_text)
        analyzer = CostAnalyzer("gpt-5")
        result = analyzer.analyze_text_and_cost(input_text, output_text)

        print("\nCost Estimation for OpenAI:" + "\n" + "-" * 50)
        for key, value in result.items():
            print(f"{key}: {value}")

        # Tokenization analysis with GPT2 tokenizer
        gpt_analyzer = TextAnalyzer("gpt2")
        analysis_result = gpt_analyzer.analyze(input_text)
        gpt_analyzer.visualize(analysis_result)
        
        # Run performance benchmarks
        run_benchmarks(input_text)
