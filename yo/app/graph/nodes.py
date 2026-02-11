"""
Nodos de LangGraph para la aplicación de IA
"""
from typing import Dict, Any


class InputHandler:
    """Nodo para manejar y validar la entrada del usuario"""
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa la entrada del usuario"""
        user_input = state.get("user_input", "").strip()
        
        # Validar que la entrada no esté vacía
        if not user_input:
            return {
                **state,
                "error": "Por favor ingresa una pregunta o mensaje",
                "input_valid": False
            }
        
        # Contar palabras para dar contexto
        word_count = len(user_input.split())
        
        return {
            **state,
            "input_valid": True,
            "input_length": word_count,
            "processed_input": user_input,
            "error": None
        }


class BrainLLM:
    """Nodo para procesar con Groq LLM"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
    
    def _get_client(self):
        """Inicializa el cliente de Groq"""
        try:
            from groq import Groq
            if self.client is None:
                self.client = Groq(api_key=self.api_key)
            return self.client
        except ImportError:
            raise ImportError("Please install groq: pip install groq")
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Genera respuesta usando Groq"""
        try:
            client = self._get_client()
            user_input = state.get("processed_input", "")
            
            # Hacer la llamada a Groq
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente IA útil y amigable. Responde de manera clara y concisa."
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1024,
            )
            
            response = chat_completion.choices[0].message.content
            
            return {
                **state,
                "llm_response": response,
                "model_used": "llama-3.3-70b-versatile",
                "error": None
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Error al generar respuesta: {str(e)}",
                "llm_response": None
            }


class PDFCreator:
    """Nodo para crear PDF con la respuesta"""
    
    def __init__(self, output_dir: str = "app/static/pdfs"):
        self.output_dir = output_dir
        import os
        os.makedirs(output_dir, exist_ok=True)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un PDF con la respuesta del LLM"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib import colors
            from datetime import datetime
            import os
            
            llm_response = state.get("llm_response", "")
            user_input = state.get("processed_input", "")
            
            if not llm_response:
                return {
                    **state,
                    "error": "No hay respuesta del LLM para generar PDF",
                    "pdf_path": None
                }
            
            # Generar nombre de archivo único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"respuesta_{timestamp}.pdf"
            pdf_path = os.path.join(self.output_dir, filename)
            
            # Crear PDF
            c = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter
            
            # Título
            c.setFont("Helvetica-Bold", 16)
            c.drawString(72, height - 72, "Respuesta de IA Assistant")
            
            # Fecha
            c.setFont("Helvetica", 10)
            c.drawString(72, height - 100, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Línea separadora
            c.line(72, height - 110, width - 72, height - 110)
            
            # Pregunta del usuario
            c.setFont("Helvetica-Bold", 12)
            c.drawString(72, height - 140, "Tu pregunta:")
            c.setFont("Helvetica", 11)
            
            # Dividir texto largo en líneas
            text_object = c.beginText(72, height - 160)
            for line in user_input.split('\n'):
                text_object.textLine(line)
            c.drawText(text_object)
            
            # Respuesta del LLM
            c.setFont("Helvetica-Bold", 12)
            c.drawString(72, height - 220, "Respuesta:")
            c.setFont("Helvetica", 11)
            
            text_object = c.beginText(72, height - 240)
            for line in llm_response.split('\n'):
                # Ajustar texto al ancho de la página
                words = line.split(' ')
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if c.stringWidth(test_line, "Helvetica", 11) < (width - 144):
                        current_line = test_line
                    else:
                        text_object.textLine(current_line)
                        current_line = word
                if current_line:
                    text_object.textLine(current_line)
            c.drawText(text_object)
            
            c.save()
            
            return {
                **state,
                "pdf_path": pdf_path,
                "pdf_filename": filename,
                "error": None
            }
            
        except ImportError:
            # Si reportlab no está disponible, crear un archivo de texto simple
            import os
            from datetime import datetime
            
            llm_response = state.get("llm_response", "")
            user_input = state.get("processed_input", "")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"respuesta_{timestamp}.txt"
            pdf_path = os.path.join(self.output_dir, filename)
            
            with open(pdf_path, 'w', encoding='utf-8') as f:
                f.write("=== Respuesta de IA Assistant ===\n\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("Tu pregunta:\n")
                f.write(user_input + "\n\n")
                f.write("Respuesta:\n")
                f.write(llm_response)
            
            return {
                **state,
                "pdf_path": pdf_path,
                "pdf_filename": filename,
                "error": None,
                "is_text_file": True
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Error al generar PDF: {str(e)}",
                "pdf_path": None
            }


class EmailDispatcher:
    """Nodo para enviar el PDF por email"""
    
    def __init__(self, email: str, app_password: str):
        self.email = email
        self.app_password = app_password
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Envía el PDF por Gmail"""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            import os
            
            recipient_email = state.get("recipient_email", "")
            pdf_path = state.get("pdf_path", "")
            user_input = state.get("processed_input", "")
            llm_response = state.get("llm_response", "")
            
            if not recipient_email:
                return {
                    **state,
                    "email_sent": False,
                    "error": "No se proporcionó email del destinatario"
                }
            
            if not pdf_path or not os.path.exists(pdf_path):
                return {
                    **state,
                    "email_sent": False,
                    "error": "No se encontró el archivo PDF para enviar"
                }
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = recipient_email
            msg['Subject'] = "Tu respuesta de IA Assistant"
            
            # Cuerpo del email
            body = f"""
¡Hola!

Aquí está la respuesta a tu pregunta de IA Assistant:

Tu pregunta: {user_input}

Respuesta: {llm_response}

¡Espero que esta información te sea útil!

Saludos,
IA Assistant
            """
            msg.attach(MIMEText(body, 'plain'))
            
            # Adjuntar archivo
            filename = os.path.basename(pdf_path)
            attachment = open(pdf_path, "rb")
            
            if state.get("is_text_file"):
                part = MIMEBase('application', 'octet-stream')
            else:
                part = MIMEBase('application', 'pdf')
            
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {filename}")
            msg.attach(part)
            
            # Enviar email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email, self.app_password)
            text = msg.as_string()
            server.sendmail(self.email, recipient_email, text)
            server.quit()
            
            attachment.close()
            
            return {
                **state,
                "email_sent": True,
                "recipient": recipient_email,
                "error": None
            }
            
        except Exception as e:
            return {
                **state,
                "email_sent": False,
                "error": f"Error al enviar email: {str(e)}"
            }


class FeedbackNode:
    """Nodo para收集 feedback del usuario"""
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa el feedback del usuario"""
        feedback = state.get("user_feedback", "")
        
        # Analizar el feedback
        if feedback:
            feedback_lower = feedback.lower()
            if any(word in feedback_lower for word in ["bueno", "excelente", "útil", "gracias", "bien"]):
                sentiment = "positive"
            elif any(word in feedback_lower for word in ["malo", "terrible", "inútil", "mal"]):
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                **state,
                "feedback_received": True,
                "feedback_text": feedback,
                "feedback_sentiment": sentiment,
                "feedback_processed": True
            }
        
        return {
            **state,
            "feedback_received": False,
            "feedback_processed": False
        }
