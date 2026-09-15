# Word-Sign Video Research Report

## Task
Find real, legitimately embeddable ASL video demonstrations for ~100 commonly-used words, to upgrade the Interpretation module's supported-word dictionary from text-only descriptions to actual embedded video of a real signer.

## Sources used, and why

**Excluded up front: Lifeprint / ASL University (Dr. Bill Vicars).** Checked their explicit policy at lifeprint.com/asl101/pages-layout/permission.htm first, since they were named as a candidate. Direct quotes: *"You can link to Lifeprint pages... but do not copy nor embed Lifeprint or other ASLU-related images or videos in your website"* and *"You do not have permission to use ASLU materials to make apps of any kind."* This rules out both their site and — since the restriction is about their material, not the hosting mechanism — his personal YouTube channel too. No Bill Vicars videos are used anywhere in the final set.

**What was used instead: individually-verified YouTube videos, embedded via YouTube's own iframe embed (`youtube.com/embed/{id}`).** YouTube's embed player is what it exists for — this is linking to the canonical hosted source, not redistributing copied files, and is the standard legitimate mechanism ed-tech sites use for exactly this purpose. Every single video was confirmed real and currently embeddable by calling YouTube's oEmbed endpoint (`https://www.youtube.com/oembed?url=...`) and getting back a valid response with title + channel — not recalled from memory or guessed. All 46 unique video IDs used in the final 114-word set were re-verified in one final bulk pass right before writing this report; all 46 returned valid oEmbed responses.

No single channel had enough individual-word coverage, so the final set draws from 13 different channels, weighted toward a few that turned out to have the broadest, most consistent coverage:

| Channel | Words covered | What it is |
|---|---|---|
| ASL LOVE | 44 | Certified Educational Interpreter, 20+ years experience, dedicated ASL vocabulary channel |
| Sign Tribe Academy | 26 | Dr. Luanne Sailors — ASL courses for autism/disability communication support |
| South Dakota School for the Deaf | 10 | An actual institutional school for the Deaf (one compilation video, "Verbs and Adjectives in ASL") |
| Able Lingo ASL | 9 | Dedicated ASL-comparison-signs channel |
| Talk with Hands | 8 | Dedicated ASL vocabulary channel |
| ASLMeredith | 4 | Certified ASL instructor, M.A. in Teaching ASL as a Foreign Language |
| Sign With JP | 4 | ASL vocabulary shorts |
| Rochester School for the Deaf | 1 | Another actual institutional school for the Deaf |
| Learn ASL With Michelle, Signing With Omar, Learn How to Sign, ASL Snapshots, Mama Mimi | 6 total | Smaller dedicated ASL-teaching channels, each individually verified |

## Efficiency note: compilation videos

Many of the source videos cover 2-10 words each (e.g. ASL LOVE's "How to Sign - Colors" covers all 10 basic colors; Sign Tribe Academy's "Question Words ASL" covers who/what/when/where/why/how in one video). Where a word's video also demonstrates other words, that's recorded in the entry's `notes` field so it's clear the embed isn't word-exclusive — the viewer will see the target word demonstrated for real, just alongside a few neighbors in the same clip.

## Final count

**114 words, all individually verified**, exceeding the ~100 target while every single entry passed real verification — nothing was padded in to hit a number.

## Words considered but NOT included (and why)

- **HATE, PROUD, WORRIED, NEW, FAST, DIRTY** — could not find a video from a channel I'd already vetted as reputable with high confidence the content matched; rather than use a lower-confidence or unfamiliar source just to hit these, they were left out. They'll fall back to fingerspelling in the app.
- **Individual pronoun distinctions (HE/SHE specifically)** — ASL pronouns are formed by pointing at/toward the actual referent (directional, not a fixed handshape per word), which one compilation video ("Pronouns in ASL," Sign Tribe Academy) explains and demonstrates for I/ME, YOU, WE, THEY. HE/SHE follows the same directional-pointing logic but wasn't separately confirmed in that video, so it was left out rather than assumed.
- **BUY, PAY, LIVE, USE, MAKE, FEEL, BELIEVE, TELL, MEET, CALL, LEARN, LISTEN, HEAR, READ, WRITE, SIGN (the word), LANGUAGE, PRACTICE, GOOD, BAD, DAY, WORLD, PHONE, BOOK, CAR, WEEK, MONTH, YEAR, NOW, LATER, ALWAYS, NEVER, SOMETIMES, MORNING, AFTERNOON, NIGHT, BATHROOM, STORE, HOSPITAL, CHURCH, CITY, GO/LEAVE-variants** — not reached within the research time budget; more compilation-video sources almost certainly exist (e.g. "150 Essential Signs" and "30 Signs You Need to Know" playlists from "Learn How to Sign" looked promising for several of these but individual word-level confirmation wasn't completed). These fall back to fingerspelling for now; a follow-up pass could extend coverage using the same verified-source methodology.

## Caveats worth knowing

- **Regional/dialectal variation**: ASL signs vary by region and community, same as spoken English has regional variants. Each video shows *a* correct, real way to sign the word from a real signer — not necessarily the only correct way.
- **Directional/pronoun signs** (I, ME, YOU, WE, THEY): these aren't fixed handshapes the way most vocabulary is — the notes field flags this on each entry.
- **MONEY** (Mama Mimi channel) is the one entry from a noticeably smaller/less-established channel than the rest of the set. Kept because the video itself is real, verified, and clearly on-topic — flagged as lower-confidence in its `notes` field rather than silently treated the same as the rest.
- Two compilation videos are reused across many words each (ASL LOVE's Colors video for 10 words, the Feelings/Emotions video for 8, the Verbs and Adjectives video for 10) — if any one of those three videos were ever taken down, it would break several words at once. Worth knowing for future maintenance.

## Addendum: upgrading compilation-video words to dedicated clips (2026-09-15)

Interpretation's communication mode only plays real sign video for words whose video is *dedicated* to that one word (see `ARCHITECTURE.md`'s "Word-level sign video" section) — the other ~96 words, including common ones like HELLO, fingerspell there instead, even though they have a real (shared/compilation) video in Learning. This addendum documents the investigation into fixing that for high-priority words, and the first one done.

**Methods investigated for deriving a clean single-sign clip from an EXISTING compilation video, so we wouldn't need new source videos at all:**
1. *Extract motion-capture landmarks by running MediaPipe over the video's frames* (same technique used for the static alphabet letters, extended across time) — requires downloading the video file. Rejected: YouTube's Terms of Service prohibit downloading video content by any means other than their own official download feature, regardless of redistribution intent. This applies even though only derived numeric data would be kept, not the video itself.
2. *Trim playback to the relevant segment using YouTube's official `start`/`end` embed parameters* (fully legitimate — still just embedding, no downloading) — requires knowing the real timestamp where a given word occurs within a compilation video. Attempted to source this from the video's caption/transcript data (also legitimate, no downloading): fetched the actual caption track for the HELLO/GOODBYE compilation video (`1d1GArVPZag`) directly from YouTube's timedtext API — it returned HTTP 200 with zero content, meaning no usable transcript exists for that video. Not a reliable general method; many ASL demonstration clips have little or no spoken narration for auto-captions to transcribe.
3. *Fabricate an approximate timestamp, or hand-animate the motion from a text description* — explicitly ruled out per this project's no-fabrication standard.

**What actually worked:** search for a genuinely dedicated single-word video from a reputable source, using the exact same oEmbed-verification method already used for the other 114 words — no new technical method needed, just more targeted sourcing per word.

**HELLO, done as proof of concept:** replaced the shared Hello/Goodbye compilation video with `543a6GRjVVk` — "Hello" ASL, posted by Springdale Public Schools' official channel (`@SpringdaleSchoolsTV`), video description "Hellstern EAST ASL Learning the word 'Hello'" (a real school ASL class clip), ~5-6 seconds long. Verified live via oEmbed on 2026-09-15. HI, GOODBYE, and BYE were left unchanged (still pointing at the original Sign Tribe Academy compilation video, still non-dedicated, still fingerspell in Interpretation) — only HELLO's entry was touched.

This was a **data-only change** (one manifest entry edited in `ml/word_signs_verified.json`) — no backend or frontend code changed. Because Learning and Interpretation both read this one shared manifest, Learning's HELLO vocabulary card automatically now shows the more precise dedicated clip too, instead of the old compilation video — an incidental improvement, not a Learning-module code change.

**Scaling beyond HELLO** (not yet done — pending direction): the same per-word search-and-verify process would need to run for each remaining high-priority word (THANK YOU, SORRY, PLEASE, HELP, LOVE, FRIEND, GOOD, BAD, YES, NO, and others). This is real per-word research effort (comparable to the original 114-word pass), not a mechanical script — each candidate video needs to actually be found and verified, not assumed to exist.
