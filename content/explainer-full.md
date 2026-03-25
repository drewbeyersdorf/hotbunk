# HotBunk - Full Explainer (2:45)

> Format: Horizontal 16:9. Mixed media: illustrations, terminal footage, animated architecture diagrams.

---

## ACT 1: THE PROBLEM (0:00 - 0:40)

### The Hook (0:00 - 0:12)

[SFX] Sonar ping. Slow fade in from black.

[VISUAL] A single number: "$200" in the center of a dark screen.

[VOICE] Two hundred dollars a month. That's a Claude Max subscription. Access to the most capable AI model on earth, running on your machine, writing code alongside you.

[VISUAL] "$200" slides up. Below it, "$30,000" appears, dimmer. "150x" connects them.

[VOICE] The same throughput on the API costs thirty thousand. The arbitrage is a hundred and fifty times.

### The Ceiling (0:12 - 0:25)

[VISUAL] A gauge. Green zone on the left, red zone on the right. The needle climbs steadily toward red.

[VOICE] But there are rate limits. Push hard for an hour. Two hours. The gauge hits red and you wait. The subscription is flat rate but the capacity is rationed.

[SFX] A soft thud. Like a door closing.

[VISUAL] The gauge needle pins at red. "THROTTLED" appears.

[VOICE] Meanwhile, your second account is sitting cold. Your teammate's account is sitting cold. Three hundred dollars a month in idle capacity. Doing nothing.

### The Waste (0:25 - 0:40)

[VISUAL] A timeline. 24 hours. One account shows 16 hours of activity and 8 hours dark. A second account shows a similar pattern, offset by a timezone.

[VOICE] You sleep eight hours. That's eight hours of premium compute sitting dark. But halfway around the world, someone just woke up. Their agents need capacity. Your account is warm. Theirs is tapped.

[VISUAL] The dark hours on both timelines pulse red. Wasted.

[VOICE] The capacity exists. It's just in the wrong place at the wrong time.

---

## ACT 2: THE METAPHOR (0:40 - 1:15)

### The Submarine (0:40 - 1:00)

[SFX] Hull groan. Submarine ambience fades in.

[VISUAL] Cross-section illustration of a submarine. Bunks stacked tight. Sailors moving between them.

[VOICE] On a submarine, a hundred and thirty people share sixty bunks. Not enough beds for everyone. Not by half. They call it hot bunking. One sailor goes on watch. Another takes the bunk they just left. The mattress is still warm from the last body.

[VISUAL] Time-lapse. The same bunk. Different sailors. Never empty. The warm orange glow never fades.

[VOICE] The bed is never cold. The bed is never empty. Because someone always needs it and someone just left it.

### The Translation (1:00 - 1:15)

[VISUAL] The submarine bunk morphs into a terminal window. Smooth transition. The warm glow becomes a cursor blinking.

[VOICE] Your Claude account is the bunk. When you sleep, someone else's agents use your headroom. When they sleep, yours use theirs. The capacity stays hot.

[SFX] Transition sound. Submarine ambience fades. Clean digital tone.

---

## ACT 3: HOW IT WORKS (1:15 - 2:00)

### The Architecture (1:15 - 1:35)

[VISUAL] Boxes draw themselves on screen. Animated, one at a time. An always-on machine in the center. Three other machines connected by lines. Labels appear as narrator names them.

[VOICE] One machine runs the orchestrator. Always on. It tracks every account in the pool. Who is active. Who is idle. Who is sleeping. Who just hit a rate limit.

[VISUAL] State labels appear next to each machine: INTERACTIVE, IDLE, SLEEPING.

[VOICE] Each machine runs a lightweight agent. It reports back. "Drew is in an interactive session." "Personal account is idle." "Work account just entered the sleep window."

### The CLI (1:35 - 1:50)

[VISUAL] Terminal footage. Real or animated recreation. Commands typed one at a time.

```
$ hotbunk status
```

[VISUAL] The status table renders. Accounts, states, headroom bars.

[VOICE] One command shows you the pool. Every account. Its state. How much headroom it has.

```
$ hotbunk submit militia -c "claude -p 'run the nightly audit'"
```

[VISUAL] The job routes to the account with the most headroom. An arrow animates from the command to the chosen account.

[VOICE] Submit a job. HotBunk picks the account with the most headroom and runs it there. You don't choose. The pool does.

### The Consent Model (1:50 - 2:00)

[VISUAL] A YAML policy file appears. Key lines highlight.

[VOICE] Every account owner sets a policy. What job types are allowed. What hours. How many concurrent. Interactive sessions always win. Automation yields the moment you sit down. No exceptions.

[SFX] Lock click.

---

## ACT 4: THE TEAM (2:00 - 2:25)

[VISUAL] Five circles appear in a row. Each one is an account. They pulse with activity, staggered like a wave. As one goes idle, the next one picks up work.

[VOICE] Five people. Five Max accounts. A thousand dollars a month total. But the pool never sleeps. Someone is always awake. Someone always has headroom. The agents keep running. The training keeps generating. The CI keeps reviewing.

[VISUAL] The wave pattern continues. A counter in the corner shows "24/7 capacity" and "0 hours idle."

[VOICE] Alone, each account hits the ceiling and waits. Together, the ceiling barely matters. The more accounts in the pool, the more total throughput everyone gets.

[SFX] Sonar ping. Rhythmic now. Steady.

[VOICE] It's cooperative. Not competitive. Everyone brings capacity. Everyone uses capacity. The pool is the product.

---

## ACT 5: CLOSE (2:25 - 2:45)

[VISUAL] The five pulsing accounts consolidate into the HotBunk logo. Below it: "Open source. MIT license."

[VOICE] HotBunk is open source. MIT license. Written in Python. Works anywhere Claude Code runs.

[VISUAL] GitHub URL appears: github.com/drewbeyersdorf/hotbunk

[VOICE] The code is on GitHub. Install it with pip. Register your accounts. Set your policy. Join a pool or start your own.

[SFX] Final sonar ping. Warmer. Resonant. Holds for a moment.

[VISUAL] Screen settles. Logo, URL, "pip install hotbunk" in terminal font. Clean.

[VOICE] The bunk is always warm.

[SFX] Silence. Fade to black.

---

**Total runtime:** ~2:45
**Tone:** Confident and unhurried. Never rushing. Let each idea land before moving to the next.
**Music:** Minimal ambient. Submarine drone in Act 2, clean digital tone in Acts 3-4. Never competing with the voice.
**Pacing:** Each section ends with a beat of silence. The viewer processes the idea before the next one starts. This is not a tutorial. This is a story.
