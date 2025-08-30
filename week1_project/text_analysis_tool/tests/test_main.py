import pytest
from utils.llm_helpers import Summarizer
from utils.analysis_feature import TextAnalyzer

# --- Sample text fixture ---
@pytest.fixture
def sample_text():
    return "This is a sample text for testing purposes. It should be short and simple."

# --- Helper to process files ---
def process_file(file_path):
    """Reads the content of a text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# --- Tests ---

def test_summarizer_summary(sample_text):
    """Test Summarizer generates output without errors."""
    summarizer = Summarizer("gemini-2.5-flash")
    summary = summarizer.summarize(sample_text)
    assert isinstance(summary, str)
    assert len(summary) > 0

def test_text_analyzer_analysis(sample_text):
    """Test TextAnalyzer tokenizes text correctly."""
    analyzer = TextAnalyzer("gpt2")
    result = analyzer.analyze(sample_text)
    assert "token_count" in result
    assert "tokens" in result
    assert result["token_count"] == len(result["tokens"])
    assert result["error"] is None

def test_process_file_with_tempfile(tmp_path, sample_text):
    """Test reading a temporary file."""
    temp_file = tmp_path / "sample.txt"
    temp_file.write_text(sample_text, encoding="utf-8")
    text = process_file(temp_file)
    assert text == sample_text

def test_process_file_missing():
    """Test error is raised for missing file."""
    missing_file = "non_existent.txt"
    with pytest.raises(FileNotFoundError):
        process_file(missing_file)
