import sqlite3
import cv2
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyzbar.pyzbar import decode


def init_db():
  conn = sqlite3.connect("sales_database.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sold_items (
            serial_number TEXT PRIMARY KEY,
            date_sold TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.commit()
  conn.close()


init_db()


def add_serial(serial):
  conn = sqlite3.connect("sales_database.db")
  cursor = conn.cursor()
  try:
    cursor.execute(
        "INSERT INTO sold_items (serial_number) VALUES (?)", (serial,)
    )
    conn.commit()
    success = True
  except sqlite3.IntegrityError:
    success = False
  conn.close()
  return success


def check_serial(serial):
  conn = sqlite3.connect("sales_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT date_sold FROM sold_items WHERE serial_number = ?", (serial,)
  )
  result = cursor.fetchone()
  conn.close()
  return result


st.set_page_config(
    page_title="سیستمی فرۆشتن و پشکنینی سێریال", layout="centered"
)
st.title("📦 سیستمی فرۆشتن و پشکنینی سێریال")

tab1, tab2, tab3 = st.tabs(
    ["➕ داخڵکردنی فرۆشتن", "🔍 پشکنین و سکان بە کامێرا", "📋 بەڕێوەبردنی خشتە"]
)

# --- TAB 1: Daxilkirina Gurgurta (Kaameraa fi Upload Qabu) ---
with tab1:
  st.header("تۆمارکردنی سێریالی فرۆشراو")

  add_option = st.radio(
      "Mallee galmeessaa filadhu:",
      ["نووسینی دەستی", "ئەپلۆدکردنی وێنە", "کامێرای ڕاستەوخۆ"],
      key="tab1_option",
  )

  scanned_add_serial = ""

  if add_option == "نووسینی دەستی":
    scanned_add_serial = st.text_input(
        "سێریال نەمبێر لێرە بنووسە:", key="input_tab1"
    )

  elif add_option == "ئەپلۆدکردنی وێنە":
    up_img = st.file_uploader(
        "Fakkii baarkoodii ykn lakkoofsa seeriyaalaa filadhu...",
        type=["jpg", "jpeg", "png"],
        key="up_add_t1",
    )
    if up_img is not None:
      file_bytes = np.asarray(bytearray(up_img.read()), dtype=np.uint8)
      opencv_image = cv2.imdecode(file_bytes, 1)
      decoded_objects = decode(opencv_image)
      if decoded_objects:
        scanned_add_serial = decoded_objects[0].data.decode("utf-8")
        st.success(f"Argame -> Seeriyaal: **{scanned_add_serial}**")
      else:
        st.warning("Baarkoodiin fakkii sana keessatti hin argamne.")

  elif add_option == "کامێرای ڕاستەوخۆ":
    cam_img = st.camera_input(
        "Galmeessuuf kaameraan fakkii kaasi", key="cam_add_t1"
    )
