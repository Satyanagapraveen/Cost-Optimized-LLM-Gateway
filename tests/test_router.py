from app.core.router import route_prompt
from app.config import config

def test_router_selects_low_tier_for_simple_prompts():
    # 1. ARRANGE
    simple_prompt = "What is the capital of France?"
    token_count = 10
    
    # 2. ACT
    selected_model = route_prompt(simple_prompt, token_count)
    
    # 3. ASSERT: It should default to the low-tier model
    assert selected_model == config.yaml.models.low_tier

def test_router_selects_high_tier_by_keyword():
    # 1. ARRANGE: A short prompt, BUT it contains a trigger keyword ("architect")
    complex_prompt = "Can you architect a Google Cloud solution?"
    token_count = 20 
    
    # 2. ACT
    selected_model = route_prompt(complex_prompt, token_count)
    
    # 3. ASSERT: 
    assert selected_model == config.yaml.models.high_tier

def test_router_selects_high_tier_by_token_length():
    # 1. ARRANGE: No keywords, BUT a massive token count
    long_prompt = "Tell me a very long story without using big words."
    token_count = 2000 
    
    # 2. ACT
    selected_model = route_prompt(long_prompt, token_count)
    
    # 3. ASSERT: The token limit should force it to the high-tier model
    assert selected_model == config.yaml.models.mid_tier