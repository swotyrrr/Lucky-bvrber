import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import pytz
from email.mime.text import MIMEText
import base64
from PIL import Image
import os
import smtplib
from email.mime.text import MIMEText

# ---------------- CONFIGURACIÓN GENERAL ----------------
st.set_page_config(page_title="💈 Lucky Bvrber 🍀", page_icon="💇", layout="wide")

# Cargar estilo CSS
try:
    with open("style/main.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("⚠️ No se encontró style/main.css")

# ---------------- IMÁGENES ----------------
def load_image(path, size=(400, 300)):
    if os.path.exists(path):
        img = Image.open(path)
        img.thumbnail(size)
        return img
    else:
        st.warning(f"No se encontró la imagen {path}")
        return None

banner = load_image("images/banner.jpg", size=(1200, 400))
if banner:
    st.image(banner, width="stretch")

# ---------------- DATOS DE SERVICIOS ----------------
SERVICIOS = {
    "Corte Clasico": {"precio": 9000, "imagen": "images/Corte_Clasico.jpg"},
    "Corte Premium": {"precio": 15000, "imagen": "images/Corte_Premium.jpg"},
    "Domicilio": {"precio": 15000, "imagen": "images/Corte_Domicilio.jpg"},
    "Tintura": {"precio": 40000, "imagen": "images/tintura.jpg"},
    "Ondulacion permanente": {"precio": 35000, "imagen": "images/Ondulado_Permanente.jpg"},
}

# ---------------- CONFIGURACIÓN DE HORARIOS ----------------
WORK_START, WORK_END, SLOT_MINUTES = 9, 18, 45
TIMEZONE = "America/Santiago"
CALENDAR_ID = "lucky.bvrber5@gmail.com"
SHEET_ID = "1z4E18eS62VUacbIHb2whKzLYTsS5zyYnRNZTqFFiQgc"
tz = pytz.timezone(TIMEZONE)

# ---------------- AUTENTICACIÓN GOOGLE ----------------
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send"
]

creds = service_account.Credentials.from_service_account_info(st.secrets["google"], scopes=SCOPES)

calendar_service = build("calendar", "v3", credentials=creds)
sheets_service = build("sheets", "v4", credentials=creds)
gmail_service = build("gmail", "v1", credentials=creds)

# ---------------- FUNCIONES ----------------
def get_day_events(service, fecha):
    start = tz.localize(datetime(fecha.year, fecha.month, fecha.day, 0, 0))
    end = start + timedelta(days=1)
    events = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    return events.get("items", [])

def is_slot_free(start, end, events):
    for event in events:
        s = event["start"].get("dateTime")
        e = event["end"].get("dateTime")
        if s and e:
            s, e = datetime.fromisoformat(s), datetime.fromisoformat(e)
            if start < e and end > s:
                return False
    return True

def create_calendar_event(service, start, end, title, desc, email):
    event = {
        "summary": title,
        "description": desc,
        "start": {"dateTime": start.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end.isoformat(), "timeZone": TIMEZONE},
    }
    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

def append_to_sheet(service, data):
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range="A1",
        valueInputOption="RAW",
        body={"values": [data]}
    ).execute()

def send_gmail_message(to, subject, body):
    # Tu correo y la app password
    gmail_user = "lucky.bvrber5@gmail.com"
    app_password = "bioz ttiy vput vbkl"

    msg = MIMEText(body)
    msg["From"] = gmail_user
    msg["To"] = to
    msg["Subject"] = subject

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, app_password)
            server.sendmail(gmail_user, to, msg.as_string())
        st.success("✅ Correo enviado correctamente.")
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")

# ---------------- INTERFAZ ----------------
st.title("💈 Reserva tu cita con 𝓛𝓾𝓬𝓴𝔂 𝐵𝓋𝓇𝒷𝑒𝓇 🍀")

nombre = st.text_input("👤 Nombre completo")
email = st.text_input("📧 Correo electrónico")
fecha = st.date_input("📅 Fecha de la cita")

if fecha:
    events = get_day_events(calendar_service, fecha)
    slots = []
    hora = WORK_START
    while hora + (SLOT_MINUTES / 60) <= WORK_END:
        start = tz.localize(datetime(fecha.year, fecha.month, fecha.day, int(hora)))
        end = start + timedelta(minutes=SLOT_MINUTES)
        if is_slot_free(start, end, events):
            slots.append(f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
        hora += SLOT_MINUTES / 60
    hora_sel = st.selectbox("🕒 Horas disponibles", slots) if slots else st.warning("Sin horarios libres.")
else:
    hora_sel = None

st.subheader("💇‍♂️ Servicios disponibles")
cols = st.columns(len(SERVICIOS))
for i, (nombre_servicio, datos) in enumerate(SERVICIOS.items()):
    with cols[i]:
        img = load_image(datos["imagen"])
        if img:
            st.image(img)
        st.markdown(f"**{nombre_servicio}** — 💵 ${datos['precio']}")

st.markdown("""**Descripción de servicios:**
- **Servicio clásico:** Corte de pelo a gusto, perfilado de cejas y barba, productos para estilizar el cabello + bebida de cortesía.
- **Servicio premium:** Incluye limpieza, exfoliación e hidratación + los mismos beneficios que clásico.
- **Servicio a domicilio:** Corte de pelo a gusto en la comodidad de su casa (valor puede variar según distancia).
""")

servicio = st.selectbox("✂️ Elige tu servicio", list(SERVICIOS.keys()))

# Inicializar sesión
if "reserva_confirmada" not in st.session_state:
    st.session_state["reserva_confirmada"] = False

# Botón de confirmación (solo se puede presionar una vez)
if st.button("📆 Confirmar reserva") and not st.session_state["reserva_confirmada"]:
    if not nombre or not email or not fecha or not hora_sel:
        st.error("Por favor, completa todos los campos.")
    else:
        start_str, end_str = hora_sel.split(" - ")
        start_dt = tz.localize(datetime.combine(fecha, datetime.strptime(start_str, "%H:%M").time()))
        end_dt = tz.localize(datetime.combine(fecha, datetime.strptime(end_str, "%H:%M").time()))
        precio = SERVICIOS[servicio]["precio"]

        if not is_slot_free(start_dt, end_dt, events):
            st.error("⛔ Ese horario ya está ocupado.")
        else:
            try:
                title = f"{servicio} — {nombre}"
                desc = f"Cliente: {nombre}\nEmail: {email}\nServicio: {servicio}\nPrecio: ${precio}"

                create_calendar_event(calendar_service, start_dt, end_dt, title, desc, email)
                append_to_sheet(sheets_service, [
                    fecha.strftime("%Y-%m-%d"), start_str, nombre, email, servicio, precio
                ])
                send_gmail_message(
                     email,
                    "Confirmación de cita — Lucky Barber",
                    f"Hola {nombre}, tu cita para {servicio} fue confirmada para el {fecha} a las {start_str}. 💈\nPrecio: ${precio}\n¡Te esperamos!"
                )
                st.success("✅ Cita confirmada y correo enviado.")
                st.session_state["reserva_confirmada"] = True
            except HttpError as e:
                st.error(f"Error en Google API: {e}")