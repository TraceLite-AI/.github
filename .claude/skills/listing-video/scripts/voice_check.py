#!/usr/bin/env python3
"""检查多段配音的语速和音调是否统一（代替"用耳朵听"的客观检查）。

用法:
  voice_check.py <音频或视频>::"这段的台词" [<文件>::"台词" ...]

对每段输出：
  开口时间 / 收声时间   人声从第几秒开始、到第几秒结束
  语速                 每秒音节数（只算出声的时间，不算停顿）
  音调                 基频中位数（Hz）
并和所有段的中位数比较，偏差超过阈值（语速 8%、音调 12%）的标 "!!"，需要重做。
需要 numpy 和 ffmpeg。
"""
import re, subprocess, sys
import numpy as np

SR, HOP, WIN = 16000, 160, 640
RATE_TOL, PITCH_TOL = 0.08, 0.12


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def syllables(text):
    """粗略数英文音节：每个单词里连续元音算一个，词尾不发音的 e 不算。"""
    n = 0
    for w in re.findall(r"[a-zA-Z']+", text.lower()):
        w = re.sub(r"e$", "", w) if len(w) > 2 and not w.endswith(('le', 'ee')) else w
        n += max(1, len(re.findall(r"[aeiouy]+", w)))
    return n


def measure(path, text):
    x = load(path)
    n = (len(x) - WIN) // HOP
    rms = np.array([np.sqrt((x[i * HOP:i * HOP + WIN] ** 2).mean()) for i in range(n)])
    voiced = rms > max(rms.max() * 0.08, 0.01)
    idx = np.where(voiced)[0]
    start, end = idx[0] * HOP / SR, idx[-1] * HOP / SR
    speech = voiced.sum() * HOP / SR
    f0 = []
    for i in idx[::3]:
        s = x[i * HOP:i * HOP + 1024]
        if len(s) < 1024:
            continue
        s = s - s.mean()
        ac = np.correlate(s, s, 'full')[1023:]
        lo, hi = SR // 350, SR // 80
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.45 * ac[0]:
            f0.append(SR / k)
    return dict(file=path, start=start, end=end, rate=syllables(text) / speech,
                pitch=float(np.median(f0)) if f0 else float('nan'))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    rows = [measure(*a.split('::', 1)) for a in sys.argv[1:]]
    rate_med = float(np.median([r['rate'] for r in rows]))
    pitch_med = float(np.nanmedian([r['pitch'] for r in rows]))
    bad = 0
    print(f"{'文件':<28}{'开口':>7}{'收声':>7}{'语速':>8}{'偏差':>8}{'音调':>8}{'偏差':>8}")
    for r in rows:
        dr, dp = r['rate'] / rate_med - 1, r['pitch'] / pitch_med - 1
        flag = ' !!' if abs(dr) > RATE_TOL or abs(dp) > PITCH_TOL else ''
        bad += bool(flag)
        print(f"{r['file'][-28:]:<28}{r['start']:>7.2f}{r['end']:>7.2f}{r['rate']:>8.2f}{dr:>+8.0%}{r['pitch']:>8.0f}{dp:>+8.0%}{flag}")
        if flag and abs(dr) > RATE_TOL:
            print(f"    → 语速偏差大：重新合成这一段，把 speed 乘以 {1 / (1 + dr):.2f}")
    print(f"中位数：语速 {rate_med:.2f} 音节/秒，音调 {pitch_med:.0f} Hz；{'全部在范围内' if not bad else str(bad) + ' 段需要重做'}")
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
