
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
import os
import pandas as pd
from datetime import datetime
import zipfile

# Crear la API
app = FastAPI()

# Definición de carpetas
BASE_DIR = "./datasets"
CAPITULO = "Cap_01"
CARPETAS = {
    "Correcta": "Imagenes_Correctas",
    "Incorrecta": "Imagenes_Incorrectas",
    "Riot_Referencia": "Imagenes_Riot_Referencia"
}
EXCEL_FILENAME = "Capitulo_1_Dataset_Metadata.xlsx"
EXCEL_PATH = os.path.join(BASE_DIR, EXCEL_FILENAME)

# Inicializar estructura de carpetas y Excel si no existen
for nombre in CARPETAS.values():
    os.makedirs(os.path.join(BASE_DIR, CAPITULO, nombre), exist_ok=True)

if not os.path.exists(EXCEL_PATH):
    df_init = pd.DataFrame(columns=[
        "NombreVisualZip", "Subtema", "Clasificacion", "Fuente",
        "AspectoCritico", "Validado", "ComentariosTecnicos"
    ])
    df_init.to_excel(EXCEL_PATH, index=False)

@app.post("/upload-image/")
async def upload_image(
    file: UploadFile = File(...),
    subtema: str = Form(...),
    clasificacion: str = Form(...),
    fuente: str = Form(...),
    aspecto: str = Form(...),
    comentarios: str = Form(""),
    validado: str = Form("Sí")
):
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    ext = os.path.splitext(file.filename)[-1]
    nombre_base = f"C01_{subtema}_{clasificacion}_{now}{ext}"
    
    carpeta_destino = os.path.join(BASE_DIR, CAPITULO, CARPETAS[clasificacion])
    ruta_final = os.path.join(carpeta_destino, nombre_base)
    
    with open(ruta_final, "wb") as f:
        f.write(await file.read())
    
    df = pd.read_excel(EXCEL_PATH)
    nueva_fila = {
        "NombreVisualZip": nombre_base,
        "Subtema": subtema,
        "Clasificacion": clasificacion,
        "Fuente": fuente,
        "AspectoCritico": aspecto,
        "Validado": validado,
        "ComentariosTecnicos": comentarios
    }
    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    df.to_excel(EXCEL_PATH, index=False)

    return JSONResponse(content={"message": "Imagen y metadatos registrados correctamente.", "filename": nombre_base})

@app.get("/generate-zip/")
def generate_zip():
    zip_path = os.path.join(BASE_DIR, "Capitulo_1_VisualDataset.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for clasificacion, carpeta in CARPETAS.items():
            carpeta_path = os.path.join(BASE_DIR, CAPITULO, carpeta)
            for root, _, files in os.walk(carpeta_path):
                for file in files:
                    ruta_completa = os.path.join(root, file)
                    arcname = os.path.relpath(ruta_completa, BASE_DIR)
                    zipf.write(ruta_completa, arcname=arcname)
        zipf.write(EXCEL_PATH, arcname=EXCEL_FILENAME)
    return FileResponse(zip_path, filename="Capitulo_1_VisualDataset.zip")

@app.get("/validate-batch/")
def validate_batch():
    df = pd.read_excel(EXCEL_PATH)
    resumen = {
        "total_imagenes": len(df),
        "por_clasificacion": df["Clasificacion"].value_counts().to_dict(),
        "por_subtema": df["Subtema"].value_counts().to_dict(),
        "errores": []
    }

    for clasificacion, carpeta in CARPETAS.items():
        carpeta_path = os.path.join(BASE_DIR, CAPITULO, carpeta)
        if not os.path.exists(carpeta_path):
            resumen["errores"].append(f"Falta carpeta: {carpeta}")
        else:
            num_files = len([f for f in os.listdir(carpeta_path) if os.path.isfile(os.path.join(carpeta_path, f))])
            if num_files == 0:
                resumen["errores"].append(f"No hay imágenes en: {carpeta}")

    return JSONResponse(content=resumen)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("eldervalor_api:app", host="0.0.0.0", port=10000, reload=False)
