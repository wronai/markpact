"""Tests for markpact generator"""

import pytest
from unittest.mock import patch, MagicMock

from markpact.generator import (
    GeneratorConfig,
    SYSTEM_PROMPT,
    get_example_prompt,
    list_example_prompts,
    EXAMPLE_PROMPTS,
)


def test_generator_config_defaults():
    """Test default configuration values"""
    config = GeneratorConfig()
    assert config.model == "ollama/qwen2.5-coder:7b"
    assert config.temperature == 0.7
    assert config.max_tokens == 4096


def test_generator_config_from_env():
    """Test configuration from environment variables"""
    with patch.dict("os.environ", {
        "MARKPACT_MODEL": "openai/gpt-4",
        "MARKPACT_API_BASE": "https://api.openai.com",
        "MARKPACT_TEMPERATURE": "0.5",
        "MARKPACT_MAX_TOKENS": "2048",
    }):
        config = GeneratorConfig.from_env()
        assert config.model == "openai/gpt-4"
        assert config.api_base == "https://api.openai.com"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048


def test_get_example_prompt():
    """Test getting example prompts by name"""
    prompt = get_example_prompt("todo-api")
    assert "REST API" in prompt
    assert "todo" in prompt.lower()


def test_get_example_prompt_unknown():
    """Test getting unknown prompt returns the input"""
    prompt = get_example_prompt("custom prompt text")
    assert prompt == "custom prompt text"


def test_list_example_prompts():
    """Test listing example prompts"""
    prompts = list_example_prompts()
    assert "todo-api" in prompts
    assert "blog-api" in prompts
    assert "url-shortener" in prompts
    assert len(prompts) >= 4


def test_system_prompt_contains_format():
    """Test system prompt contains markpact format instructions"""
    assert "markpact:deps" in SYSTEM_PROMPT
    assert "markpact:file" in SYSTEM_PROMPT
    assert "markpact:run" in SYSTEM_PROMPT


def test_example_prompts_dict():
    """Test EXAMPLE_PROMPTS dictionary"""
    assert isinstance(EXAMPLE_PROMPTS, dict)
    for name, desc in EXAMPLE_PROMPTS.items():
        assert isinstance(name, str)
        assert isinstance(desc, str)
        assert len(desc) > 10  # meaningful description


@pytest.mark.skipif(True, reason="Requires litellm and running LLM server")
def test_generate_contract_integration():
    """Integration test for contract generation (skipped by default)"""
    from markpact.generator import generate_contract
    
    config = GeneratorConfig(
        model="ollama/qwen2.5-coder:7b",
        api_base="http://localhost:11434",
    )
    
    content = generate_contract(
        "Simple hello world Flask app",
        config=config,
        verbose=True,
    )
    
    assert "```markpact:" in content
    assert "flask" in content.lower()


def test_generate_contract_mock():
    """Test generate_contract with mocked litellm"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """# Hello World

```markpact:deps python
flask
```

```markpact:file python path=app.py
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"
```

```markpact:run python
flask run --port 5000
```
"""
    
    with patch("markpact.generator.litellm") as mock_litellm:
        with patch("markpact.generator.LITELLM_AVAILABLE", True):
            mock_litellm.completion.return_value = mock_response
            
            from markpact.generator import generate_contract
            
            content = generate_contract("Hello world Flask app")
            
            assert "markpact:deps" in content
            assert "flask" in content.lower()
            assert "markpact:run" in content
