from diffusers import StableDiffusionPipeline

print("Conectando con HuggingFace...")
print("Iniciando descarga del modelo (son aprox. 4-5 GB, puede demorar)...")

# Al tener tqdm instalado, esta línea generará las barras de progreso automáticamente
pipeline = StableDiffusionPipeline.from_pretrained('runwayml/stable-diffusion-v1-5')

print("\nDescarga y carga en memoria finalizada.")
