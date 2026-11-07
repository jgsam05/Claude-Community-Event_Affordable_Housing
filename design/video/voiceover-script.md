# OCA demo video: voiceover script (30 seconds)

Read calmly, at a steady pace. About 62 words. Leave a short pause at each scene change. The captions in the video match these lines.

| Time | Line |
| --- | --- |
| 0.4 to 3.8 s | Finding land for affordable homes means digging through scattered records. |
| 4.5 to 8.7 s | OCA is built for the people who build and protect affordable housing. |
| 9.4 to 14.4 s | Enter an Orange County ZIP code, and see the sites worth a closer look. |
| 15.4 to 19.6 s | A ranked list and a map. Filter by the kind of site. |
| 20.4 to 24.6 s | Three scores per site, with sources and confidence. |
| 28.3 to 30.0 s | OCA. Find where affordable homes can go. |

## Recording notes

- Record in a quiet room, close to the mic, with a soft cloth or blanket nearby to dampen echo.
- Record each line as its own take so you can nudge timing.
- Keep music about 20 dB below the voice, and sound effects below the music.
- Keep the captions on. Many judges watch without sound.

## Rebuild the video with sound effects

```bash
node render.js ../../scratch/frames          # video frames and silent MP4
python3 make_audio.py oca-sfx.wav             # typing, click and transition sounds
ffmpeg -i oca-demo.mp4 -i oca-sfx.wav -c:v copy -c:a aac -b:a 192k -shortest oca-demo-sfx.mp4
```
