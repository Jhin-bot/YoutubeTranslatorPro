import srt
def export_srt(segments, out_path):
    subs = []
    for i, seg in enumerate(segments):
        subs.append(srt.Subtitle(index=i+1, start=seg['start'], end=seg['end'], content=seg['text']))
    open(out_path, 'w').write(srt.compose(subs))
