import json, sys, os, re, time, urllib.parse, urllib.request
UA = "ShortsFactoryBot/1.0 (https://github.com/pro172348-byte/media-tmp)"
API = "https://commons.wikimedia.org/w/api.php"
def get(url, tries=3):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            err = e; time.sleep(2 + 3 * k)
    raise err
def strip(h): return re.sub(r"<[^>]+>", "", h or "").strip()
req = json.load(open("req.json"))
os.makedirs("media", exist_ok=True)
meta = {}
for q in req.get("queries", []):
    params = dict(action="query", format="json", generator="search", gsrnamespace=6,
                  gsrsearch=q["q"] + " filetype:bitmap", gsrlimit=q.get("n", 6),
                  prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=q.get("w", 1080))
    try:
        data = json.loads(get(API + "?" + urllib.parse.urlencode(params)))
    except Exception as e:
        meta[q["id"]] = {"error": str(e)}; continue
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    for k, p in enumerate(pages):
        ii = p["imageinfo"][0]; em = ii.get("extmetadata", {})
        name = f'{q["id"]}_{k}.jpg'
        try:
            open("media/" + name, "wb").write(get(ii.get("thumburl") or ii["url"]))
        except Exception as e:
            continue
        meta[name] = dict(query=q["q"], title=p["title"], page=ii.get("descriptionurl"),
                          license=strip(em.get("LicenseShortName", {}).get("value")),
                          artist=strip(em.get("Artist", {}).get("value"))[:120],
                          desc=strip(em.get("ImageDescription", {}).get("value"))[:200],
                          w=ii.get("width"), h=ii.get("height"))
        time.sleep(0.3)
for u in req.get("urls", []):
    try: open("media/" + u["name"], "wb").write(get(u["url"])); meta[u["name"]] = {"url": u["url"]}
    except Exception as e: meta[u["name"]] = {"error": str(e)}
json.dump(meta, open("media/meta.json", "w"), ensure_ascii=False, indent=1)
