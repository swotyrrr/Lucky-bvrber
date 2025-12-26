# Barber Web - Reservas con Google Calendar + Sheets

Este proyecto es una aplicación hecha en Streamlit que permite:

- Reservar horas
- Guardarlas en Google Sheets
- Crear eventos en Google Calendar
- Cancelar reservas actualizando su estado en la hoja de cálculo

## ✔ Deploy en Render

### 1. Subir a GitHub

Sube todo el proyecto excepto el archivo JSON de Google.
No incluyas credenciales en el repositorio.

### 2. Crear servicio Web en Render

- Crear cuenta en https://render.com  
- New → Web Service  
- Elige el repositorio  
- Runtime: **Python 3**
- Build Command:
```bash
pip install -r requirements.txt