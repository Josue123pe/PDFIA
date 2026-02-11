"""
Definición del grafo de LangGraph
"""
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from graph.nodes import InputHandler, BrainLLM, PDFCreator, EmailDispatcher, FeedbackNode
import os
from dotenv import load_dotenv

load_dotenv()

# Definir el tipo de estado
class AppState(TypedDict):
    """Estado de la aplicación"""
    user_input: str
    recipient_email: str
    user_feedback: str
    input_valid: bool = False
    processed_input: str = ""
    llm_response: str = None
    pdf_path: str = None
    pdf_filename: str = None
    email_sent: bool = False
    error: str = None


def create_app_graph():
    """Crea el grafo de la aplicación con los 5 nodos"""
    
    # Inicializar nodos
    input_handler = InputHandler()
    brain_llm = BrainLLM(api_key=os.getenv("GROQ_API_KEY", ""))
    pdf_creator = PDFCreator(output_dir="app/static/pdfs")
    email_dispatcher = EmailDispatcher(
        email=os.getenv("GMAIL_EMAIL", ""),
        app_password=os.getenv("GMAIL_APP_PASSWORD", "")
    )
    feedback_node = FeedbackNode()
    
    # Crear el grafo con StateGraph
    workflow = StateGraph(AppState)
    
    # Agregar nodos
    workflow.add_node("input_handler", input_handler)
    workflow.add_node("brain_llm", brain_llm)
    workflow.add_node("pdf_creator", pdf_creator)
    workflow.add_node("email_dispatcher", email_dispatcher)
    workflow.add_node("feedback_node", feedback_node)
    
    # Definir punto de entrada
    workflow.set_entry_point("input_handler")
    
    # Definir transiciones
    workflow.add_edge("input_handler", "brain_llm")
    workflow.add_edge("brain_llm", "pdf_creator")
    
    # Condicional: si hay email, ir a email_dispatcher, sino a feedback_node
    def should_send_email(state: AppState) -> str:
        """Determina si enviar email o no"""
        if state.get("recipient_email"):
            return "email_dispatcher"
        return "feedback_node"
    
    workflow.add_conditional_edges(
        "pdf_creator",
        should_send_email,
        {
            "email_dispatcher": "email_dispatcher",
            "feedback_node": "feedback_node"
        }
    )
    
    workflow.add_edge("email_dispatcher", "feedback_node")
    workflow.add_edge("feedback_node", END)
    
    # Compilar el grafo
    app = workflow.compile()
    
    return app


def run_graph(user_input: str, recipient_email: str = None, user_feedback: str = None) -> Dict[str, Any]:
    """Ejecuta el grafo con los datos proporcionados"""
    
    # Inicializar estado inicial
    initial_state = AppState(
        user_input=user_input,
        recipient_email=recipient_email or "",
        user_feedback=user_feedback or ""
    )
    
    print(f"DEBUG: Initial state: {initial_state}")
    
    try:
        # Crear y ejecutar el grafo
        app = create_app_graph()
        
        # Ejecutar el grafo
        final_state = app.invoke(initial_state)
        
        print(f"DEBUG: Final state: {final_state}")
        
        return final_state if final_state else initial_state
        
    except Exception as e:
        import traceback
        error_msg = f"Error al ejecutar el grafo: {str(e)}"
        print(f"DEBUG: {error_msg}")
        traceback.print_exc()
        return {"error": error_msg, "llm_response": None}
