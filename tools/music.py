"""Procedural chiptune soundtrack for Oasis. Writes seamless loops as 16-bit mono WAV."""
import numpy as np, wave, random

SR = 22050
OUT = '/home/claude/game/assets/sound/music/'


def note_freq(n):            # MIDI note -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


def osc(kind, f, t, duty=0.5):
    ph = (f * t) % 1.0
    if kind == 'square': return np.where(ph < duty, 1.0, -1.0)
    if kind == 'tri': return 4 * np.abs(ph - 0.5) - 1
    if kind == 'saw': return 2 * ph - 1
    return np.sin(2 * np.pi * ph)


def env(n, a=0.01, d=0.08, s=0.6, r=0.08):
    t = np.arange(n) / SR
    L = n / SR
    e = np.ones(n) * s
    e[t < a] = t[t < a] / a
    m = (t >= a) & (t < a + d)
    e[m] = 1 - (1 - s) * (t[m] - a) / d
    rel = t > L - r
    e[rel] *= np.clip((L - t[rel]) / r, 0, 1)
    return e


def render(track_len, events):
    buf = np.zeros(int(track_len * SR) + SR)
    for start, dur, freq, kind, vol, duty, shape in events:
        n = int(dur * SR)
        t = np.arange(n) / SR
        w = osc(kind, freq, t, duty) * env(n, *shape) * vol
        i = int(start * SR)
        buf[i:i + n] += w
    # wrap the tail into the start so the loop is seamless
    L = int(track_len * SR)
    tail = buf[L:]
    buf = buf[:L]
    buf[:len(tail)] += tail
    return buf


def noise_hits(track_len, times, vol, dur=0.04, seed=0):
    rng = np.random.default_rng(seed)
    buf = np.zeros(int(track_len * SR) + SR)
    for s in times:
        n = int(dur * SR)
        hit = rng.uniform(-1, 1, n) * np.exp(-np.arange(n) / (n / 5)) * vol
        i = int(s * SR); buf[i:i + n] += hit
    L = int(track_len * SR); tail = buf[L:]; buf = buf[:L]; buf[:len(tail)] += tail
    return buf


def kick(track_len, times, vol):
    buf = np.zeros(int(track_len * SR) + SR)
    for s in times:
        n = int(0.12 * SR); t = np.arange(n) / SR
        f = 110 * np.exp(-t * 30) + 45
        w = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18) * vol
        i = int(s * SR); buf[i:i + n] += w
    L = int(track_len * SR); tail = buf[L:]; buf = buf[:L]; buf[:len(tail)] += tail
    return buf


def song(name, bpm, root, scale, progression, bars_per_chord, seed, lead='square', bass='tri',
         lead_vol=0.16, swing=0.0, drums=True, pad=False, motif_len=8, density=0.75):
    rng = random.Random(seed)
    beat = 60 / bpm
    bar = beat * 4
    total_bars = len(progression) * bars_per_chord
    L = total_bars * bar
    ev = []
    deg = lambda d: root + scale[d % len(scale)] + 12 * (d // len(scale))
    # build two melodic motifs (A and B) out of 8th notes, repeated with variation -> memorable
    def motif():
        m, d = [], rng.choice([2, 4, 7])
        for i in range(motif_len):
            if rng.random() < density:
                d += rng.choice([-2, -1, -1, 1, 1, 2, 0, 3, -3])
                d = max(0, min(11, d))
                m.append(d)
            else:
                m.append(None)
        return m
    A, B = motif(), motif()
    form = [A, A, B, A] * (total_bars // 4 + 1)
    for b in range(total_bars):
        chord = progression[b // bars_per_chord]
        mot = form[b]
        start = b * bar
        # lead: 8th notes; nudge toward chord tones on strong beats
        for i, d in enumerate(mot):
            if d is None: continue
            if i % 4 == 0:
                tones = [chord, chord + 2, chord + 4, chord + 7]
                d = min(tones, key=lambda x: abs(x - d))
            st = start + i * beat / 2 + (swing * beat / 2 if i % 2 else 0)
            length = beat / 2 * (2 if (i + 1 < len(mot) and mot[i + 1] is None) else 1) * 0.95
            ev.append((st, length, note_freq(deg(d) + 12), lead, lead_vol, 0.25 if lead == 'square' else 0.5, (0.005, 0.05, 0.55, 0.05)))
        # bass: root on 1 & 3, fifth on the off-beats
        for i in range(4):
            n = deg(chord) - 12 if i % 2 == 0 else deg(chord + 4) - 12
            ev.append((start + i * beat, beat * 0.9, note_freq(n), bass, 0.26, 0.5, (0.005, 0.05, 0.7, 0.05)))
        # arpeggio / pad
        if pad:
            for k, off in enumerate([0, 2, 4]):
                ev.append((start, bar, note_freq(deg(chord + off)), 'tri', 0.05, 0.5, (0.4, 0.2, 0.8, 0.4)))
        else:
            for i in range(8):
                off = [0, 2, 4, 2][i % 4]
                ev.append((start + i * beat / 2, beat / 2 * 0.6, note_freq(deg(chord + off)), 'square', 0.045, 0.125, (0.002, 0.03, 0.3, 0.02)))
    mix = render(L, ev)
    if drums:
        hats = [b * bar + i * beat / 2 for b in range(total_bars) for i in range(8)]
        kicks = [b * bar + i * beat for b in range(total_bars) for i in (0, 2)]
        snares = [b * bar + i * beat for b in range(total_bars) for i in (1, 3)]
        mix += noise_hits(L, hats, 0.035, 0.025, seed) + noise_hits(L, snares, 0.09, 0.09, seed + 1) + kick(L, kicks, 0.35)
    mix = mix / max(1e-6, np.max(np.abs(mix))) * 0.8
    pcm = (mix * 32767).astype('<i2')
    with wave.open(OUT + name + '.wav', 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    print(name, round(L, 1), 's')


if __name__ == '__main__':
    import os; os.makedirs(OUT, exist_ok=True)
    MAJOR = [0, 2, 4, 5, 7, 9, 11]
    DORIAN = [0, 2, 3, 5, 7, 9, 10]
    # title: hopeful, steady
    song('title', 96, 60, MAJOR, [0, 4, 5, 3, 0, 4, 3, 4], 2, seed=7, lead='square', density=0.7)
    # village: bouncy, warm, swung
    song('village', 112, 62, MAJOR, [0, 3, 4, 0, 5, 3, 4, 4], 2, seed=21, lead='tri', lead_vol=0.22, swing=0.25, density=0.8)
    # grove: slow, mysterious, pads, no drums
    song('grove', 78, 57, DORIAN, [0, 6, 3, 4, 0, 6, 4, 0], 2, seed=99, lead='sine', lead_vol=0.24, drums=False, pad=True, density=0.55)
