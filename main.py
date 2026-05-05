import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types
import asyncio
from dotenv import load_dotenv
from groq import Groq

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Asistente Inteligente Multimodal",
    description="API que procesa texto e interactúa con archivos de forma independiente.",
    version="4.0.0"
)

# Inicializar clientes
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELOS_TEXTO = ["llama-3.3-70b-versatile"]
MODELO_MULTIMODAL = "gemini-2.5-flash"

@app.get("/api/modelos")
def obtener_modelos():
    return {
        "modelos_texto": MODELOS_TEXTO,
        "modelo_multimodal": MODELO_MULTIMODAL
    }

@app.post("/api/consultar-texto")
async def consultar_texto(prompt: str = Form(...), modelo: str = Form(...)):
    respuesta_texto = ""
    try:
        if modelo == MODELO_MULTIMODAL:
            response = await asyncio.to_thread(
                genai_client.models.generate_content,
                model=MODELO_MULTIMODAL,
                contents=prompt
            )
            respuesta_texto = response.text
        elif modelo in MODELOS_TEXTO:
            chat_completion = await asyncio.to_thread(
                groq_client.chat.completions.create,
                messages=[{"role": "user", "content": prompt}],
                model=modelo,
            )
            respuesta_texto = chat_completion.choices[0].message.content
        else:
            raise HTTPException(status_code=400, detail="Modelo no reconocido.")

        return {
            "modelo_utilizado": modelo,
            "prompt": prompt,
            "respuesta": respuesta_texto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en servidor de texto: {str(e)}")

@app.post("/api/consultar-multimodal")
async def consultar_multimodal(
    prompt: str = Form(...),
    modelo: str = Form(...),
    file: UploadFile = File(...)
):
    respuesta_texto = ""
    try:
        if modelo != MODELO_MULTIMODAL:
            raise HTTPException(status_code=400, detail=f"Para analizar archivos debes seleccionar {MODELO_MULTIMODAL}")
        
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen o PDF válido.")

        file_bytes = await file.read()
        
        contenido_multimodal = [
            prompt,
            types.Part.from_bytes(data=file_bytes, mime_type=file.content_type)
        ]

        response = await asyncio.to_thread(
            genai_client.models.generate_content,
            model=MODELO_MULTIMODAL,
            contents=contenido_multimodal
        )
        respuesta_texto = response.text

        return {
            "modelo_utilizado": modelo,
            "prompt": prompt,
            "respuesta": respuesta_texto
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en servidor de archivos: {str(e)}")

# Interfaz HTML integrada dentro de la misma API
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Asistente Inteligente Multimodal</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background-color: #121214;
                color: #e1e1e6;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .card {
                background-color: #1f1f23;
                border: 1px solid #323238;
            }
            .form-control, .form-select {
                background-color: #2a2a2e;
                border: 1px solid #323238;
                color: #fff;
            }
            .form-control:focus, .form-select:focus {
                background-color: #2a2a2e;
                color: #fff;
                border-color: #4CAF50;
                box-shadow: 0 0 0 0.25rem rgba(76, 175, 80, 0.25);
            }
            .btn-success {
                background-color: #4CAF50;
                border: none;
            }
            .btn-success:hover {
                background-color: #45a049;
            }
            #resultado {
                background-color: #2a2a2e;
                border-left: 5px solid #4CAF50;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                color: #fff;
                white-space: pre-wrap;
            }
        </style>
    </head>
    <body class="py-5">
        <div class="container" style="max-width: 600px;">
            <h2 class="mb-4 text-center">📄 Asistente Inteligente Multimodal</h2>
            
            <div class="card p-4 shadow-sm">
                <div class="mb-3">
                    <label for="modelo" class="form-label">Selecciona el modelo:</label>
                    <select id="modelo" class="form-select">
                        <option value="gemini-2.5-flash">gemini-2.5-flash</option>
                        <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                    </select>
                </div>

                <div class="mb-3">
                    <label for="prompt" class="form-label">Escribe tu pregunta o instrucción:</label>
                    <textarea id="prompt" class="form-control" rows="4" placeholder="Ej: Resuelve este problema matemático paso a paso..."></textarea>
                </div>

                <div class="mb-3">
                    <label class="form-label">Adjuntar archivo (Opcional):</label>
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="tipoArchivo" id="tipoSin" value="sin" checked onclick="toggleArchivo()">
                        <label class="form-check-label" for="tipoSin">Sin archivo</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="tipoArchivo" id="tipoImg" value="img" onclick="toggleArchivo()">
                        <label class="form-check-label" for="tipoImg">Imagen</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="tipoArchivo" id="tipoPdf" value="pdf" onclick="toggleArchivo()">
                        <label class="form-check-label" for="tipoPdf">Documento PDF</label>
                    </div>
                </div>

                <div class="mb-3 d-none" id="archivoContainer">
                    <label for="fileInput" class="form-label" id="labelArchivo">Sube un archivo:</label>
                    <input type="file" class="form-control" id="fileInput">
                </div>

                <button class="btn btn-success w-100" onclick="enviarConsulta()">🚀 Enviar consulta</button>
            </div>

            <div id="resultado" class="d-none"></div>
        </div>

        <script>
            const API_URL = "http://127.0.0.1:8000/api";

            function toggleArchivo() {
                const contenedor = document.getElementById('archivoContainer');
                const label = document.getElementById('labelArchivo');
                if (document.getElementById('tipoSin').checked) {
                    contenedor.classList.add('d-none');
                } else {
                    contenedor.classList.remove('d-none');
                    if (document.getElementById('tipoImg').checked) {
                        label.innerText = "Sube una imagen:";
                        document.getElementById('fileInput').accept = "image/*";
                    } else {
                        label.innerText = "Sube un PDF:";
                        document.getElementById('fileInput').accept = "application/pdf";
                    }
                }
            }

            async function enviarConsulta() {
                const modelo = document.getElementById('modelo').value;
                const prompt = document.getElementById('prompt').value;
                const fileInput = document.getElementById('fileInput').files[0];
                const resultadoDiv = document.getElementById('resultado');

                if (!prompt && !fileInput) {
                    alert("Por favor, escribe una pregunta o sube un archivo.");
                    return;
                }

                resultadoDiv.classList.remove('d-none');
                resultadoDiv.innerText = "Consultando a la IA...";

                const formData = new FormData();
                formData.append('prompt', prompt || "Analiza este archivo.");
                formData.append('modelo', modelo);

                let url = `${API_URL}/consultar-texto`;
                if (fileInput) {
                    url = `${API_URL}/consultar-multimodal`;
                    formData.append('file', fileInput);
                }

                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();

                    if (response.ok) {
                        resultadoDiv.innerText = data.respuesta || JSON.stringify(data);
                    } else {
                        resultadoDiv.innerText = "Error: " + (data.detail || JSON.stringify(data));
                    }
                } catch (error) {
                    resultadoDiv.innerText = "Error al conectar con la API (Verifica que el puerto 8000 esté abierto). Detalles: " + error.message;
                }
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)