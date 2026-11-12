# SCION SYSTEM INSTRUCTION · TALK: TWO JELLYFISH, TWO LANGUAGES

Where: TALK in the dock, or `bonus/jellyorchestra.html?talk=1` (Bolas edition `/bolas/cities/?talk=1`).

## 1. Thesis
The cast could sing a line in five languages, but only lines prepared in advance. Talk is live: you say
something, your jellyfish says it, and a second jellyfish says it again in another language. With a second
person, each of you has one jelly and the two of you hold a conversation neither could have alone.

## 2. What you do
- **Choose languages:** I SPEAK and THE OTHER SPEAKS (English, 中文, Español, Português, አማርኛ).
- **Say something:** type and press SAY, press one of the ready phrases, or press MIC and speak.
- **Hear it twice:** your jelly says your line; the other says the translation. The words light as they are said.
- **Choose a style and a dance:** MY JELLY (ten species) and MY DANCE (sway, bounce, spin, pulse, still).
- **Make a room for two:** a QR code and a link appear. The other person scans it, and each of you has one jelly.

## 3. How a line is translated, in order
1. **Phrasebook** (built in, nothing leaves the device): 16 everyday phrases and the 50 song titles, in all five.
2. **Your browser's own translator**, if it has one. If it does not answer in 3.5 seconds it is skipped.
3. **MyMemory**, a public translation service, only when ONLINE TRANSLATION is lit. The line you typed is sent to it.
   It is off until you turn it on, and the panel says so.
4. If none of these can do it, your jelly says the line and the other stays silent, with a note saying why.

## 4. How a room works
- The QR code is a link with a six-character room name.
- The two browsers find each other through a public meeting point (PeerJS's free server), then talk directly.
- Only the words, the translation and your style travel. Each device makes both voices itself.
- When someone joins, THE OTHER SPEAKS locks to their language and their jelly takes their style and dance.
- Two tabs on one machine can use each other without the meeting point: add `&local=1`.

## 5. What leaves your device
| Action | Goes where |
|---|---|
| Typing, phrasebook | nowhere |
| ONLINE TRANSLATION on | the typed line, to MyMemory |
| MIC | your voice, to your browser's speech service |
| A room | words and style, to the other person; the room name, to the meeting point |

## 6. What was checked (local copy, headless browser)
- A phrasebook line: "hello" → 你好, both jellies spoke.
- A line not in the phrasebook with online off: the note appeared and only one jelly spoke.
- The same line with online on and **the service replaced by a stand-in**: the translation was used and spoken.
- A room between two tabs (`&local=1`): both joined; each saw the other's species and dance; "thank you" arrived
  as 谢谢 on the guest; 再见 arrived as "goodbye" on the host. The QR code drew (41 modules a side). No errors.

## 7. What was not checked
- **The real MyMemory service and the real PeerJS meeting point.** This machine cannot reach outside hosts, so
  neither was called. A room between two phones is therefore untested. If the meeting point fails, the panel says so.
- MIC: no speech service in the test browser. Not every browser has one; the button hides where it does not.
- The QR code was drawn but not scanned.
- Sound. Also: after the stills I moved the two jellies further from the camera (they filled the frame) and did
  not re-shoot.

## 8. Limits
- The voice is the same engine as the cast, so every caveat about pronunciation applies, more so for free text.
- Lines are capped at 120 characters. One line at a time.
- A room is for two.

## 9. Next
- A room for more than two, and a way to see who is there.
- Let a line be sung to the current song instead of spoken.
- Carry talk into the game: the other person is in the same place.
