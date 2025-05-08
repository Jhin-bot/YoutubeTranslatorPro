import whisper
from functools import lru_cache
from multiprocessing import Pool, cpu_count

@lru_cache(maxsize=4)
def load_model(name): return whisper.load_model(name)

def transcribe_file(args):
    path, model = args
    m = load_model(model)
    return m.transcribe(path)

def transcribe(audio_path, model='small'):
    with Pool(cpu_count()) as p:
        result = transcribe_file((audio_path, model))
    return result
