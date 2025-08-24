import time
from typing import Dict, List, Tuple
from nltk.tokenize import word_tokenize
from transformers import AutoTokenizer
from config import ModelCosts

class CostAnalyzer:
    def __init__(self, model_name: str):
        """
        Initialize with model name and automatically set costs.
        Supported models: 'gemini', 'gpt'
        """
        self.model_name = model_name.lower()
        if "gemini" in self.model_name:
            self.input_cost = ModelCosts.GM_I_COST
            self.output_cost = ModelCosts.GM_O_COST
        elif "gpt" in self.model_name:
            self.input_cost = ModelCosts.GPT_I_COST
            self.output_cost = ModelCosts.GPT_O_COST
        else:
            raise ValueError("Unsupported model name for cost analysis.")

    def analyze_text_and_cost(self, input_text: str, output_text: str) -> dict:
        """
        Tokenizes input and output texts, counts tokens, and estimates total cost.
        """
        input_tokens = word_tokenize(input_text) if input_text else []
        output_tokens = word_tokenize(output_text) if output_text else []

        input_count = len(input_tokens)
        output_count = len(output_tokens)

        input_token_cost = (input_count / 1_000_000) * self.input_cost
        output_token_cost = (output_count / 1_000_000) * self.output_cost
        total_cost = input_token_cost + output_token_cost

        return {
            "input_tokens": input_count,
            "output_tokens": output_count,
            "total_cost": total_cost,
        }


class TextAnalyzer:
    def __init__(self, model_name: str):
        """
        Initialize the analyzer with a specific tokenizer model.
        Args:
            model_name (str): e.g., 'bert-base-uncased', 'gpt2'
        """
        self.model_name = model_name
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        except Exception as e:
            raise ValueError(f"Error loading tokenizer {model_name}: {e}")

    def analyze(self, text: str) -> dict:
        """
        Tokenizes text, calculates token statistics, and handles edge cases.
        """
        if not text:
            return {
                'model_name': self.model_name,
                'token_count': 0,
                'tokens': [],
                'error': 'Input text is empty.'
            }

        try:
            tokens = self.tokenizer.tokenize(text)
            return {
                'model_name': self.model_name,
                'token_count': len(tokens),
                'tokens': tokens,
                'error': None
            }
        except Exception as e:
            return {
                'model_name': self.model_name,
                'token_count': None,
                'tokens': None,
                'error': f"Error during tokenization: {e}"
            }

    def visualize(self, analysis_result: dict):
        """
        Displays token boundaries and statistics in a readable format.
        """
        if analysis_result.get('error'):
            print(f"Error for {analysis_result['model_name']}: {analysis_result['error']}")
            return

        model_name = analysis_result['model_name']
        token_count = analysis_result['token_count']
        tokens = analysis_result['tokens']

        print(f"\n--- Tokenization Analysis for {model_name} ---")
        print(f"Total tokens: {token_count}")
        print("\nToken Boundaries:")
        print(" | ".join(tokens))
        print("\n" + "="*50)


class ModelBenchmark:
    """
    A class to benchmark the performance of different language models.
    Measures latency, tokens per second, and other relevant metrics.
    """
    
    def __init__(self, model_name: str):
        """
        Initialize the benchmark with a model name.
        
        Args:
            model_name: Name of the model to benchmark (e.g., 'gpt2', 'gpt-3.5-turbo')
        """
        self.model_name = model_name
        self.start_time = 0
        self.end_time = 0
        self.input_tokens = 0
        self.output_tokens = 0
    
    def start_timer(self):
        """Start the benchmark timer."""
        self.start_time = time.time()
    
    def stop_timer(self):
        """Stop the benchmark timer."""
        self.end_time = time.time()
    
    def record_token_counts(self, input_text: str, output_text: str):
        """
        Record the number of input and output tokens.
        
        Args:
            input_text: The text sent to the model
            output_text: The text received from the model
        """
        self.input_tokens = len(word_tokenize(input_text)) if input_text else 0
        self.output_tokens = len(word_tokenize(output_text)) if output_text else 0
    
    def get_metrics(self) -> Dict[str, float]:
        """
        Calculate and return benchmark metrics.
        
        Returns:
            Dictionary containing various performance metrics
        """
        if not self.start_time or not self.end_time:
            raise ValueError("Benchmark not completed. Call start_timer() and stop_timer() first.")
            
        total_time = self.end_time - self.start_time
        total_tokens = self.input_tokens + self.output_tokens
        
        return {
            'model': self.model_name,
            'total_time_seconds': total_time,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'tokens_per_second': total_tokens / total_time if total_time > 0 else 0,
            'input_tokens_per_second': self.input_tokens / total_time if total_time > 0 else 0,
            'output_tokens_per_second': self.output_tokens / total_time if total_time > 0 else 0,
            'latency_seconds': total_time
        }
    
    @staticmethod
    def compare_benchmarks(benchmarks: List[Dict]) -> str:
        """
        Generate a comparison report from multiple benchmark results.
        
        Args:
            benchmarks: List of benchmark result dictionaries
            
        Returns:
            Formatted string comparing all benchmarks
        """
        if not benchmarks:
            return "No benchmark results to compare."
            
        # Sort by total time (ascending)
        sorted_benchmarks = sorted(benchmarks, key=lambda x: x['total_time_seconds'])
        
        report = [
            "\n" + "="*60,
            "MODEL PERFORMANCE COMPARISON",
            "="*60
        ]
        
        # Find the fastest model
        fastest = sorted_benchmarks[0]
        
        for idx, bench in enumerate(sorted_benchmarks, 1):
            speed_diff = ""
            if idx > 1:
                speed_diff = f" ({((bench['total_time_seconds'] / fastest['total_time_seconds']) - 1) * 100:.1f}% slower)"
                
            report.extend([
                f"\n{idx}. {bench['model']}:",
                f"   Total Time: {bench['total_time_seconds']:.4f}s{speed_diff}",
                f"   Input Tokens: {bench['input_tokens']}",
                f"   Output Tokens: {bench['output_tokens']}",
                f"   Tokens/Second: {bench['tokens_per_second']:.2f}",
                f"   Latency: {bench['latency_seconds']:.4f}s"
            ])
            
        report.append("\n" + "="*60)
        return "\n".join(report)
