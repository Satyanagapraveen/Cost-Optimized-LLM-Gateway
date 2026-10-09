from app.config import config

def route_prompt(prompt:str, token_count: int)-> str:
    cleaned_prompt_lower=prompt.lower()
    rules=config.yaml.routing_rules
    models=config.yaml.models

    for rule in rules:
        if rule.condition=="contains_keyword":
            if rule.keywords and any(keyword in cleaned_prompt_lower for keyword in rule.keywords):
                target_model_string=getattr(models, rule.target_tier)
                return target_model_string
        elif rule.condition=="max_tokens_exceeded":
            if rule.threshold is not None and token_count>rule.threshold:
                target_model_string=getattr(models,rule.target_tier)
                return target_model_string
        elif rule.condition=="match_all":
            target_model_string=getattr(models,rule.target_tier)
            return target_model_string
    return models.low_tier
            
