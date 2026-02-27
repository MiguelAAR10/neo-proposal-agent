import asyncio
import sys
from pathlib import Path

# Añadir el backend al path
sys.path.append(str(Path(__file__).parent / "backend"))

from src.agent.graph import graph
from src.agent.state import ProposalState

async def test_bcp_flow():
    print("\n--- 🧪 TEST DE FLUJO COMPLETO: CASO BCP (MVP V2) ---")
    
    # Simulación de Inputs Iniciales del Consultor
    inputs = {
        "empresa": "BCP",
        "rubro": "Banca",
        "area": "Operaciones",
        "problema": "Necesitamos automatizar la conciliación de pagos masivos que hoy toma 5 días y tiene muchos errores manuales.",
        "switch": "both",
        "casos_seleccionados_ids": []
    }
    
    config = {"configurable": {"thread_id": "test_thread_bcp_001"}}
    
    print(f"\n1. Iniciando Intake y Retrieve para: {inputs['empresa']}...")
    
    # Primera ejecución: hasta el interrupt
    async for event in graph.astream(inputs, config=config, stream_mode="values"):
        state = event

    print(f"✅ Casos encontrados: {len(state.get('casos_encontrados', []))}")
    if state.get("perfil_cliente"):
        print(f"✅ Perfil del cliente recuperado: {state['perfil_cliente'].get('notas')}")

    # Seleccionamos un caso
    if state.get("casos_encontrados"):
        selected_ids = [state["casos_encontrados"][0]["id"]]
    else:
        # Dummy si no hay nada (aunque debería haber)
        selected_ids = ["NEO-011"]
    
    print(f"\n2. Consultor selecciona casos: {selected_ids}")
    
    # ACTUALIZAMOS EL ESTADO antes de continuar
    graph.update_state(config, {"casos_seleccionados_ids": selected_ids})
    
    # CONTINUAMOS pasando None como entrada
    print("\n3. Generando propuesta final...")
    async for event in graph.astream(None, config=config, stream_mode="values"):
        final_state = event

    if final_state.get("propuesta_final"):
        print("\n4. 📄 PROPUESTA GENERADA POR GEMINI (Orientada al BCP):")
        print("-" * 50)
        print(final_state["propuesta_final"])
        print("-" * 50)
    else:
        print(f"❌ Error en la generación: {final_state.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_bcp_flow())
