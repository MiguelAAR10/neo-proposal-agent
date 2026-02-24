"""
Diagnóstico rápido de embeddings con Google GenAI.
Ejecuta: python diagnose_embeddings.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("DIAGNÓSTICO DE EMBEDDINGS")
print("=" * 60)

# 1. Python info
print(f"\n🐍 Python: {sys.executable}")
print(f"   Versión: {sys.version}")

# 2. Package versions
print("\n📦 Versiones de paquetes:")
try:
    import google.genai as genai
    print(f"   google-genai: {genai.__version__}")
except ImportError:
    print("   google-genai: NO INSTALADO")
except AttributeError:
    print("   google-genai: instalado (sin __version__)")

try:
    import google.generativeai as genai_old
    print(f"   google-generativeai: {genai_old.__version__}")
except ImportError:
    print("   google-generativeai: NO INSTALADO")
except AttributeError:
    print("   google-generativeai: instalado (sin __version__)")

try:
    import langchain_google_genai
    print(f"   langchain-google-genai: {langchain_google_genai.__version__}")
except ImportError:
    print("   langchain-google-genai: NO INSTALADO")
except AttributeError:
    print("   langchain-google-genai: instalado (sin __version__)")

# 3. API Key check
api_key = os.environ.get("GEMINI_API_KEY", "")
if api_key:
    print(f"\n🔑 GEMINI_API_KEY: ...{api_key[-6:]}")
else:
    print("\n🔑 GEMINI_API_KEY: ❌ NO CONFIGURADA")
    sys.exit(1)

# 4. List available embedding models via the SDK
print("\n🔍 Modelos de embedding disponibles:")
try:
    from google import genai as genai_client
    client = genai_client.Client(api_key=api_key)
    for model in client.models.list():
        name = model.name if hasattr(model, 'name') else str(model)
        if 'embed' in name.lower():
            methods = getattr(model, 'supported_generation_methods', [])
            print(f"   ✅ {name}  (methods: {methods})")
except Exception as e:
    print(f"   Error listando modelos con google-genai Client: {e}")
    # Fallback: try the old SDK
    try:
        import google.generativeai as genai_old
        genai_old.configure(api_key=api_key)
        for model in genai_old.list_models():
            if 'embed' in model.name.lower():
                print(f"   ✅ {model.name}  (methods: {model.supported_generation_methods})")
    except Exception as e2:
        print(f"   Error con google-generativeai: {e2}")

# 5. Direct test with different model names
print("\n🧪 Probando embeddings directamente:")
candidates = [
    "models/text-embedding-004",
    "text-embedding-004",
    "models/gemini-embedding-exp-03-07",
    "models/embedding-001",
    "embedding-001",
]

for model_name in candidates:
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        emb = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=api_key,
        )
        result = emb.embed_query("hello world")
        print(f"   ✅ {model_name} -> OK (dim={len(result)})")
        break  # Found a working model
    except Exception as e:
        err_msg = str(e)[:100]
        print(f"   ❌ {model_name} -> {err_msg}")

print("\n" + "=" * 60)
