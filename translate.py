from deep_translator import GoogleTranslator
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, max=10))
def translate(text, target):
    return GoogleTranslator(source='auto', target=target).translate(text)
