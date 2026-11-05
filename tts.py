import json, os, base64, wave, time, urllib.request, urllib.error
KEY = os.environ.get("GEMINI_API_KEY", "")
MODELS = ["gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts"]
os.makedirs("audio", exist_ok=True)
log = []
if not KEY:
    log.append("NO_KEY: secret GEMINI_API_KEY is empty")
req = json.load(open("tts.json"))
for it in req["items"] if KEY else []:
    prompt = (it.get("style", "") + "\n\n" + it["text"]).strip()
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": it.get("voice", "Charon")}}}}}
    done = False
    for m in ([it["model"]] if it.get("model") else MODELS):
        for attempt in range(3):
            try:
                r = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                    data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
                with urllib.request.urlopen(r, timeout=180) as resp:
                    d = json.loads(resp.read())
                part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
                pcm = base64.b64decode(part["data"])
                rate = 24000
                mt = part.get("mimeType", "")
                if "rate=" in mt: rate = int(mt.split("rate=")[1].split(";")[0])
                with wave.open("audio/" + it["name"], "wb") as w:
                    w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
                log.append(f"OK {it['name']} model={m} sec={len(pcm)/2/rate:.1f}")
                done = True; break
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="ignore")[:300].replace(KEY, "***")
                log.append(f"HTTP {e.code} {it['name']} model={m}: {msg}")
                if e.code in (429, 500, 503): time.sleep(20 * (attempt + 1)); continue
                break
            except Exception as e:
                log.append(f"ERR {it['name']} model={m}: {str(e)[:200]}"); time.sleep(5)
        if done: break
    time.sleep(3)
open("audio/_log.txt", "w").write("\n".join(log) + "\n")
