# Script rules (from the approved reels)

## Shape: about 13 lines, 60-75 s after the x1.12 speed-up
| # | beat | example (Hinglish caption) |
|---|---|---|
| 0 | **Hook**: the most shocking fact, as if telling a friend | "Bihar mein kuch logon ne, asli thane se sirf 500 meter door, apna nakli thana khol diya." |
| 1 | Make it worse | "Aur bhai, 8 mahine tak kisi ko pata hi nahi chala!" |
| 2-3 | Who / where, in pictures | "Jagah? Banka ka Anurag guest house. Hotel ka kamra, ban gaya thana." |
| 4-6 | **Escalation**: the scam step by step, numbers on screen | "Shikayat likhwani hai? 100 se 500 rupaye." |
| 7-9 | How it fell apart: getting caught, the escape | "Wahan asli thanedar ne dekha, kamar pe police wali pistol nahi, desi katta hai!" |
| 10-11 | **Twist**: "Ab asli twist suno." Something that flips the story | "Madam ne khud naukri ke liye 90 hazaar ki rishwat di thi..." |
| 12 | **CTA**: send + like, tied to the story | "Ye reel us dost ko bhejo, jo bolta hai, meri upar tak setting hai. Aur like kar do, warna nakli thane bhej dunga!" |

## Voice of the narrator
- A friend roasting the story over chai: short questions and answers ("Kaam kya tha?", "Aur company ne kya kiya?"),
  "bhai", "socho", "matlab", "sabka baap nikla". Mock the con man's audacity and the system's sleepiness, never the victims.
- **No gaali.** Clean roast humour reads better and gets shared more.
- Legends and unproven bits: "कहते हैं" (kehte hain).
- Each line 8-25 words, natural pauses at commas (Chatterbox breathes there). One idea per line.

## The three text fields
- `text`: Devanagari, what the voice reads and what Whisper checks. Hindi words in Devanagari, English loanwords in
  Devanagari too (टैंक, कंपनी, गेस्ट हाउस).
- `roman`: the same words in the same order, in English letters, the way people type Hinglish ("bhai", "kya", "nahi",
  "pata hi nahi chala"). Digits for numbers. Punctuation is fine here (captions strip it).
- `say` (optional): a respelling for the voice only, e.g. an extra comma for a pause, or a word Chatterbox misreads.

## Chatterbox pronunciation gotchas
- Numbers: always words in `text`. It misreads some: "तेईस" came out as 30, "डेढ़ सौ" as 200. Write "एक सौ पचास" not
  "डेढ़ सौ", and check every number in the "heard" report.
- Abbreviations get slurred ("एम बी"): write the full word ("मेगाबाइट").
- Very long lines can grow a babbling tail that Whisper doesn't transcribe. `best_take.py` drops takes that are much longer
  than the others; still listen to any line the report flags.

## Tragedies
Respectful tone throughout, `"music": "bed"`, no jokes about the dead or injured, no cartoon victims, numbers stated
plainly, end on a dark memorial card and a lesson ("rules changed after this") instead of a joke CTA.

## Topic ideas
Victor Lustig sold the Eiffel Tower twice · the Captain of Köpenick · Alcatraz 1962 escape · the Hitler Diaries hoax ·
Frank Abagnale · the fake SBI branch (Chhattisgarh 2024) · the fake embassy (Ghaziabad) · Sher Singh Rana's Tihar escape ·
the Pig War · the guards at the spa.
