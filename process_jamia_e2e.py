import os
import json
import urllib.request
import urllib.parse
import uuid
import argparse

# Setup constants
MICRO_APP_URL = "https://micro-app-57l9.onrender.com/upload"
LOCAL_RENDER_URL = "http://127.0.0.1:8000/render-html"
DOCX_FILENAME = "Copy of Jamia Islamia Online MBA program.docx"
CACHE_PATH = "backend/generated/temp_debug.json"
OUTPUT_HTML_NAME = "jamia-islamia-jamia-millia-islamia-online-mba.dc.html"

def upload_docx_to_microapp(file_path):
    print(f"Uploading '{file_path}' to micro app parser at '{MICRO_APP_URL}'...")
    boundary = uuid.uuid4().hex
    
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    body = []
    # File field
    filename = os.path.basename(file_path)
    body.append(f"--{boundary}".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode("utf-8"))
    body.append(b"Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    body.append(b"")
    body.append(file_content)
    
    body.append(f"--{boundary}--".encode("utf-8"))
    body.append(b"")
    
    body_data = b"\r\n".join(body)
    
    req = urllib.request.Request(MICRO_APP_URL, data=body_data)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Content-Length", str(len(body_data)))
    
    try:
        with urllib.request.urlopen(req) as res:
            response_data = res.read().decode("utf-8")
            return json.loads(response_data)
    except Exception as e:
        print(f"Error during upload request: {e}")
        raise

def render_local_html(acf_payload):
    print(f"Sending ACF data to local backend endpoint at '{LOCAL_RENDER_URL}'...")
    
    # Construct RenderRequest payload
    render_payload = {
        "acf_data": acf_payload,
        "images": {}
    }
    
    json_data = json.dumps(render_payload).encode("utf-8")
    
    req = urllib.request.Request(LOCAL_RENDER_URL, data=json_data)
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req) as res:
            headers = res.info()
            disposition = headers.get("Content-Disposition", "")
            print(f"Response Content-Disposition: {disposition}")
            html_content = res.read().decode("utf-8")
            return html_content
    except Exception as e:
        print(f"Error during render request: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="E2E docx-to-page generator using micro-app parser and local renderer backend.")
    parser.add_argument("--force", action="store_true", help="Force upload & re-parse of the docx file instead of using cache.")
    args = parser.parse_args()
    
    workspace_root = os.getcwd()
    docx_path = os.path.join(workspace_root, DOCX_FILENAME)
    cache_file = os.path.join(workspace_root, CACHE_PATH)
    output_html_path = os.path.join(workspace_root, OUTPUT_HTML_NAME)
    
    if not os.path.exists(docx_path):
        print(f"Error: '{DOCX_FILENAME}' not found in the workspace root: {workspace_root}")
        return
        
    parsed_data = None
    
    # 1. Try to load from cache
    if os.path.exists(cache_file) and not args.force:
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            # Verify it is the right file
            if cached.get("filename") == DOCX_FILENAME and "payload" in cached:
                print(f"✓ Found cached response in '{CACHE_PATH}'. Using it to avoid external API costs.")
                parsed_data = cached
        except Exception as e:
            print(f"Warning: Failed to read cache file ({e}). Proceeding to re-parse.")
            
    # 2. Upload and parse if needed
    if parsed_data is None:
        print("Starting parser workflow via micro app...")
        try:
            parsed_data = upload_docx_to_microapp(docx_path)
            # Store in cache
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            print(f"✓ Successfully stored parsed JSON response in '{CACHE_PATH}'.")
        except Exception as e:
            print(f"Error: Parser pipeline failed: {e}")
            return
            
    # 3. Call local backend renderer
    acf_payload = parsed_data["payload"]
    try:
        html_content = render_local_html(acf_payload)
        
        # 4. Save rendered HTML to workspace root
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✓ E2E Generation complete! HTML file generated and saved to root folder:")
        print(f"  --> {output_html_path}")
        print(f"  Size: {len(html_content)} bytes")
    except Exception as e:
        print(f"Error: Rendering pipeline failed: {e}")

if __name__ == "__main__":
    main()
