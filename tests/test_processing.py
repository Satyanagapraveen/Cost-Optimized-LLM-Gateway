from app.core.preprocessing import process_prompt

def test_preprocessing_cleans_messy_text():
    messy_input= "   Hello \n\n \t World!   "
    cleaned_text,token_count=process_prompt(messy_input)
    assert cleaned_text=="Hello \n\n World!"
    assert token_count>0


