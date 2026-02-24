"""
Diagnóstico RAW - va directo a la API de Google sin SDK.
Ejecuta: python diagnose_raw.py
"""
import json
import os
import sys
import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    print("❌ GEMINI_API_KEY no está configurada en .env")
    sys.exit(1)

print(f"🔑 API Key: ...{api_key[-6:]}")
print(f"🐍 Python: {sys.executable}")

# --- Check package versions ---
print("\n📦 Versiones de paquetes:")
for pkg in ["google-genai", "google-generativeai", "langchain-google-genai", "google-ai-generativelanguage"]:
    try:
        from importlib.metadata import version as pkg_version
        print(f"   {pkg}: {pkg_version(pkg)}")
    except Exception:
        print(f"   {pkg}: no instalado")

# --- Test 1: Verify API key works (list models via REST) ---
print("\n" + "=" * 60)
print("TEST 1: Verificar API key con REST API (v1beta)")
print("=" * 60)

url_v1beta = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
url_v1 = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"

for label, url in [("v1beta", url_v1beta), ("v1", url_v1)]:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            models = data.get("models", [])
            embed_models = [
                m["name"] for m in models 
                if any("embed" in method.lower() for method in m.get("supportedGenerationMethods", []))
            ]
            print(f"\n✅ API {label} funciona! ({len(models)} modelos totales)")
            print(f"   Modelos de embedding disponibles:")
            for em in embed_models:
                methods = [m for m in next(mod for mod in models if mod["name"] == em).get("supportedGenerationMethods", [])]
                print(f"     • {em}  ({', '.join(methods)})")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"\n❌ API {label} falló: HTTP {e.code}")
        print(f"   {body[:300]}")
    except Exception as e:
        print(f"\n❌ API {label} error: {e}")

# --- Test 2: Try embedding directly via REST ---
print("\n" + "=" * 60)
print("TEST 2: Probar embedding directo vía REST")
print("=" * 60)

test_models = [
    "text-embedding-004",
    "embedding-001",
    "gemini-embedding-exp-03-07",
]

for model_name in test_models:
    for api_ver in ["v1beta", "v1"]:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:embedContent?key={api_key}"
        payload = json.dumps({
            "model": f"models/{model_name}",
            "content": {"parts": [{"text": "hello world"}]}
        }).encode("utf-8")
        
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                dim = len(data.get("embedding", {}).get("values", []))
                print(f"   ✅ {api_ver}/{model_name} -> OK (dim={dim})")
                break  # This model works, skip other api version
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            short = json.loads(body).get("error", {}).get("message", body)[:120] if body else str(e)
            print(f"   ❌ {api_ver}/{model_name} -> HTTP {e.code}: {short}")
        except Exception as e:
            print(f"   ❌ {api_ver}/{model_name} -> {str(e)[:120]}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO COMPLETO")
print("=" * 60)
