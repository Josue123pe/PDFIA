"""
Aplicación Flask con LangGraph
"""
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from graph.graph import run_graph
import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")

# Asegurar que existe el directorio de PDFs
os.makedirs("app/static/pdfs", exist_ok=True)


@app.route("/")
def index():
    """Página principal con el formulario"""
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    """Procesa la solicitud del usuario"""
    user_input = request.form.get("user_input", "").strip()
    recipient_email = request.form.get("recipient_email", "").strip()
    user_feedback = request.form.get("user_feedback", "").strip()
    
    if not user_input:
        flash("Por favor ingresa una pregunta o mensaje", "error")
        return redirect(url_for("index"))
    
    try:
        # Ejecutar el grafo
        state = run_graph(
            user_input=user_input,
            recipient_email=recipient_email,
            user_feedback=user_feedback
        )
        
        # Verificar errores
        if state.get("error"):
            flash(state["error"], "error")
            return redirect(url_for("index"))
        
        # Preparar datos para la plantilla
        result_data = {
            "user_input": user_input,
            "llm_response": state.get("llm_response", ""),
            "pdf_path": state.get("pdf_path", ""),
            "pdf_filename": state.get("pdf_filename", ""),
            "email_sent": state.get("email_sent", False),
            "recipient_email": recipient_email,
            "feedback_processed": state.get("feedback_processed", False),
            "feedback_sentiment": state.get("feedback_sentiment", "")
        }
        
        return render_template("result.html", **result_data)
        
    except Exception as e:
        import traceback
        error_msg = f"Error al procesar: {str(e)}"
        # Imprimir error en terminal para debug
        print(f"DEBUG: {error_msg}")
        traceback.print_exc()
        flash(error_msg, "error")
        return redirect(url_for("index"))


@app.route("/download/<filename>")
def download_pdf(filename):
    """Permite descargar el PDF generado"""
    try:
        return send_file(
            f"app/static/pdfs/{filename}",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f"Error al descargar: {str(e)}", "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
