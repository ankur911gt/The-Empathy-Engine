#!/usr/bin/env python3
"""
CLI interface for The Empathy Engine.

Usage:
    python cli.py "I'm so happy about this!"
    python cli.py --emotion anger "This is a test sentence."
    python cli.py --output my_speech.mp3 "Hello world"
"""

import argparse
import asyncio
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(
        description="🎭 The Empathy Engine — Emotion-driven TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "I finally got into my dream university!"
  python cli.py "She's gone and I have nothing left."
  python cli.py --emotion anger "This is a neutral sentence."
  python cli.py --output speech.mp3 "Hello world"
        """,
    )
    parser.add_argument("text", help="Text to analyze and speak")
    parser.add_argument("--emotion", "-e", help="Force a specific emotion (skip detection)")
    parser.add_argument("--output", "-o", default="output.mp3", help="Output filename (default: output.mp3)")
    parser.add_argument("--no-play", action="store_true", help="Don't auto-play the audio")

    args = parser.parse_args()

    asyncio.run(run_pipeline(args.text, args.emotion, args.output, not args.no_play))


async def run_pipeline(text: str, forced_emotion: str | None, output_file: str, auto_play: bool):
    start = time.time()

    # Step 1: Detect emotion
    print("\n🎭 The Empathy Engine")
    print("=" * 50)
    print(f"\n📝 Input: \"{text}\"")
    print(f"\n🧠 Step 1: Detecting emotion...", end=" ", flush=True)

    from app.services.emotion import detect_emotion, EmotionResult, VALID_EMOTIONS

    if forced_emotion and forced_emotion in VALID_EMOTIONS:
        emotion_result = EmotionResult(
            emotion=forced_emotion,
            intensity=0.85,
            all_scores={e: (0.85 if e == forced_emotion else 0.02) for e in VALID_EMOTIONS},
            detection_source="forced",
        )
        print(f"Forced → {forced_emotion}")
    else:
        emotion_result = await detect_emotion(text)
        print(f"Detected → {emotion_result.emotion} ({emotion_result.intensity:.0%})")

    # Show all scores
    sorted_scores = sorted(emotion_result.all_scores.items(), key=lambda x: x[1], reverse=True)
    print(f"\n   Emotion Scores:")
    for emo, score in sorted_scores:
        bar = "█" * int(score * 30)
        marker = " ◄" if emo == emotion_result.emotion else ""
        print(f"   {emo:>10s}  {bar:<30s} {score:.1%}{marker}")

    # Step 2: Map voice parameters
    print(f"\n🎛️  Step 2: Mapping voice parameters...", end=" ", flush=True)

    from app.services.mapper import get_voice_config

    voice_config = get_voice_config(emotion_result.emotion, emotion_result.intensity)
    print("Done")
    print(f"   Rate:   {voice_config.rate}")
    print(f"   Pitch:  {voice_config.pitch}")
    print(f"   Volume: {voice_config.volume}")
    print(f"   Voice:  {voice_config.voice}")

    # Step 3: Preprocess text
    print(f"\n✍️  Step 3: Enriching text...", end=" ", flush=True)

    from app.services.text_preprocessor import preprocess_text

    processed = preprocess_text(text, emotion_result.emotion, emotion_result.intensity)
    print("Done")
    if processed != text:
        print(f"   Before: {text}")
        print(f"   After:  {processed}")
    else:
        print(f"   No changes (emotion handled by voice params only)")

    # Step 4: Generate SSML
    print(f"\n🏷️  Step 4: Generating SSML...", end=" ", flush=True)

    from app.services.ssml_generator import generate_ssml

    ssml = generate_ssml(processed, voice_config, emotion_result.emotion, emotion_result.intensity)
    print("Done")

    # Step 5: Synthesize speech
    print(f"\n🔊 Step 5: Synthesizing speech...", end=" ", flush=True)

    from app.services.audio import synthesize_speech

    audio_bytes, filename = await synthesize_speech(processed, voice_config)

    # Save to user-specified output
    import shutil
    from pathlib import Path
    from app.core.config import settings

    src = Path(settings.audio_output_dir) / filename
    if src.exists():
        shutil.copy2(src, output_file)
    else:
        Path(output_file).write_bytes(audio_bytes)

    elapsed = time.time() - start
    file_size = len(audio_bytes)
    print(f"Done")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"✅ Audio saved: {output_file}")
    print(f"   File size:       {file_size / 1024:.1f} KB")
    print(f"   Processing time: {elapsed:.1f}s")
    print(f"   Pipeline:        Emotion → Voice Map → Text Enrich → SSML → TTS")
    print()

    # Auto-play on Windows
    if auto_play:
        try:
            if sys.platform == "win32":
                os.startfile(output_file)
            elif sys.platform == "darwin":
                os.system(f"afplay {output_file}")
            else:
                os.system(f"xdg-open {output_file}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
