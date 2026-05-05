import streamlit as st
import requests
from PIL import Image

st.set_page_config(
    page_title="IA Multimodal y Documentos",
    page_icon="📄",
    layout="centered"
)

# APUNTAR CORRECTAMENTE AL PUERTO 8000 DEL BACKEND
API_BASE_URL = "http://127.0.0.1:8000/api"
API_TEXTO_URL = f"{API_BASE_URL}/consultar-texto"
API_MULTIMODAL_URL = f"{API_BASE_URL}/consultar-multimodal"
API_MODELOS_URL = f"{API_BASE_URL}/modelos"

st.title("📄 Asistente Inteligente Multimodal")

tab1, tab2 = st.tabs(["💬 Consultar Texto", "📎 Analizar Archivos (Imagen o PDF)"])

modelos_texto = ["llama-3.3-70b-versatile"]
modelo_multimodal = "gemini-2.5-flash"
todos_los_modelos = modelos_texto + [modelo_multimodal]

try:
    response_modelos = requests.get(API_MODELOS_URL, timeout=3)
    if response_modelos.status_code == 200:
        data_modelos = response_modelos.json()
        modelos_texto = data_modelos.get("modelos_texto", [])
        modelo_multimodal = data_modelos.get("modelo_multimodal", "gemini-2.5-flash")
        todos_los_modelos = modelos_texto + [modelo_multimodal]
except:
    pass

with tab1:
    st.subheader("Consultar información con texto o imágenes")
    
    # Selector de modelo y entrada de texto
    modelo_texto = st.selectbox("Selecciona el modelo:", modelos_texto + [modelo_multimodal], key="sel_modelo_texto")
    prompt_texto = st.text_area("Escribe tu pregunta o instrucción:", height=100, key="prompt_texto")
    
    # Subida opcional de imagen/archivo dentro de la consulta de texto
    tipo_archivo_texto = st.radio("¿Deseas adjuntar un archivo a tu consulta?", ("Sin archivo", "Imagen", "Documento PDF"), key="tipo_arch_texto")
    archivo_texto = None
    
    if tipo_archivo_texto == "Imagen":
        archivo_texto = st.file_uploader("Sube una imagen de apoyo", type=["png", "jpg", "jpeg"], key="img_texto")
    elif tipo_archivo_texto == "Documento PDF":
        archivo_texto = st.file_uploader("Sube un PDF de apoyo", type=["pdf"], key="pdf_texto")
        
    if archivo_texto is not None and tipo_archivo_texto == "Imagen":
        st.image(archivo_texto, caption="Imagen cargada", use_container_width=True)

    if st.button("🚀 Enviar consulta", key="btn_texto"):
        if not prompt_texto.strip() and archivo_texto is None:
            st.error("Escribe tu pregunta o sube un archivo para continuar.")
        else:
            with st.spinner("Consultando a la IA..."):
                try:
                    # Si hay un archivo adjunto, mandarlo por el endpoint multimodal
                    if archivo_texto is not None:
                        archivo_texto.seek(0)
                        files = {"file": (archivo_texto.name, archivo_texto.read(), archivo_texto.type)}
                        data = {"prompt": prompt_texto, "modelo": modelo_texto}
                        
                        response = requests.post(API_MULTIMODAL_URL, data=data, files=files)
                    else:
                        # Si es solo texto, mandarlo por el endpoint de texto
                        response = requests.post(API_TEXTO_URL, data={"prompt": prompt_texto, "modelo": modelo_texto})
                        
                    if response.status_code == 200:
                        resultado = response.json()
                        st.success("¡Respuesta recibida!")
                        st.markdown(
                            f"""
                            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50; color: black;">
                                {resultado['respuesta']}
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    else:
                        st.error(f"Error: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Error al conectar con la API (verifica que el backend corra en el puerto 8000): {str(e)}")

with tab2:
    st.subheader("Analizar herramientas avanzadas")
    modelo_archivo = st.selectbox("Selecciona el modelo para archivos:", [modelo_multimodal], key="sel_modelo_archivo")
    prompt_archivo = st.text_area("Escribe una instrucción para tu archivo:", height=80, value="Analiza este archivo.", key="prompt_archivo")
    
    tipo_archivo = st.radio("Elige el tipo de archivo:", ("Imagen", "Documento PDF"), key="tipo_arch_tab2")
    archivo = None
    
    if tipo_archivo == "Imagen":
        archivo = st.file_uploader("Sube una imagen", type=["png", "jpg", "jpeg"], key="img_tab2")
    else:
        archivo = st.file_uploader("Sube un PDF", type=["pdf"], key="pdf_tab2")

    if archivo is not None and tipo_archivo == "Imagen":
        st.image(archivo, caption="Imagen cargada", use_container_width=True)
        
    if st.button("🚀 Analizar archivo", key="btn_archivo"):
        if archivo is None:
            st.error("Por favor, sube un archivo para analizar.")
        else:
            with st.spinner("Analizando documento..."):
                try:
                    archivo.seek(0)
                    files = {"file": (archivo.name, archivo.read(), archivo.type)}
                    data = {"prompt": prompt_archivo, "modelo": modelo_archivo}
                    
                    response = requests.post(
                        API_MULTIMODAL_URL,
                        data=data,
                        files=files
                    )
                    if response.status_code == 200:
                        resultado = response.json()
                        st.success("¡Respuesta recibida!")
                        st.markdown(
                            f"""
                            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #2196F3; color: black;">
                                {resultado['respuesta']}
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    else:
                        st.error(f"Error: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"Error al conectar con la API: {str(e)}")