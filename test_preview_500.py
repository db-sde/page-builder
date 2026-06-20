import json
import urllib.request
import traceback

LOCAL_PREVIEW_URL = "http://127.0.0.1:8000/preview-html"
CACHE_PATH = "backend/generated/temp_debug.json"

def main():
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cached = json.load(f)
        
        # Simulate Screen2Review.jsx's fields state which excludes objects/arrays
        raw_acf = cached["payload"]
        acf_data = {}
        for k, v in raw_acf.items():
            if k in ['slug', 'page_type', 'university_slug', 'parent_slug']:
                continue
            if isinstance(v, (dict, list)):
                continue
            acf_data[k] = str(v) if v is not None else ""
        
        request_body = {
            "acf_data": acf_data,
            "images": {}
        }
        
        json_data = json.dumps(request_body).encode("utf-8")
        req = urllib.request.Request(LOCAL_PREVIEW_URL, data=json_data)
        req.add_header("Content-Type", "application/json")
        
        print(f"Posting to {LOCAL_PREVIEW_URL}...")
        with urllib.request.urlopen(req) as res:
            print("Response Code:", res.getcode())
            print("Response Content Length:", len(res.read()))
            
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}")
        print("Response body:")
        print(e.read().decode("utf-8"))
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
