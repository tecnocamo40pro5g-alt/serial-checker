import sqlite3
import cv2
import numpy as np
import pandas as pd
import streamlit as st
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


def delete_serial(serial):
  conn = sqlite3.connect("sales_database.db")
  cursor = conn.cursor()
  cursor.execute("DELETE FROM sold_items WHERE serial_number = ?", (serial,))
  conn.commit()
  conn.close()


def update_serial(old_serial, new_serial):
  conn = sqlite3.connect("sales_database.db")
  cursor = conn.cursor()
  try:
    cursor.execute(
        "UPDATE sold_items SET serial_number = ? WHERE serial_number = ?",
        (new_serial, old_serial),
    )
    conn.commit()
    success = True
  except sqlite3.IntegrityError:
    success = False
  conn.close()
  return success


st.set_page_config(
    page_title="سیستمی پشکنینی سێریال نەمبێر", layout="centered"
)
st.title("📦 سیستمی بەڕێوەبردن و پشکنینی مەواد بە سێریال")

tab1, tab2, tab3 = st.tabs([
    "➕ داخڵکردنی مەواد",
    "🔍 پشکنین و سکان",
    "📋 بینین و دەستکاریکردنی خشتە",
])

with tab1:
  st.header("تۆمارکردنی سێریال نەبەری فرۆشراو")
  manual_serial = st.text_input(
      "سێریال نەمبێر لێرە بنووسە یان سکانی بکە:", key="input_tab1"
  )
  if st.button("تۆمارکردن"):
    if manual_serial.strip() != "":
      is_saved = add_serial(manual_serial.strip())
      if is_saved:
        st.success(
            f"✅ سەرکەوتوو بوو! سێریال ({manual_serial}) تۆمارکرا لەگەڵ کاتی"
            " ئێستا."
        )
      else:
        st.warning(
            f"⚠️ ئاگاداری: سێریال ({manual_serial}) پێشتر تۆمار کراوە!"
        )
    else:
      st.error("تکایە سێریال نەمبێر بنووسە.")

  st.subheader("دواین مەوادە فرۆشراوەکان:")
  try:
    conn = sqlite3.connect("sales_database.db")
    df = pd.read_sql_query(
        "SELECT * FROM sold_items ORDER BY date_sold DESC LIMIT 5", conn
    )
    conn.close()
    if not df.empty:
      st.dataframe(df, use_container_width=True)
    else:
      st.info("هیچ مەوادێک تا ئێستا تۆمار نەکراوە.")
  except Exception:
    pass

with tab2:
  st.header("پشکنینی مەواد و زانینی بەرواری فرۆشتن")
  option = st.radio(
      "ڕێگەی پشکنین هەڵبژێرە:",
      ["نووسینی دەستی / سکانەر", "ئەپلۆدکردنی وێنە", "کامێرای ڕاستەوخۆ"],
  )

  def show_result(serial_no):
    res = check_serial(serial_no)
    if res:
      sale_date = res[0]
      st.error(
          f"❌ ئەم مەوادە (سێریال: **{serial_no}**) **فرۆشراوە**!\n\n📅"
          f" **بەروار و کاتی فرۆشتن:** `{sale_date}`"
      )
    else:
      st.success(
          f"✅ ئەم مەوادە (سێریال: **{serial_no}**) **نەفرۆشراوە** (لە"
          " مەخزەنە / نوێیە)."
      )

  if option == "نووسینی دەستی / سکانەر":
    check_input = st.text_input(
        "سێریال نەمبێر بنووسە یان سکانەر بەکاربهێنە بۆ پشکنین:", key="check_input"
    )
    if check_input:
      show_result(check_input.strip())

  elif option == "ئەپلۆدکردنی وێنە":
    uploaded_image = st.file_uploader(
        "وێنەی بارکۆد یان سێریال نەمبێر هەڵبژێرە...",
        type=["jpg", "jpeg", "png"],
        key="img_up",
    )
    if uploaded_image is not None:
      file_bytes = np.asarray(bytearray(uploaded_image.read()), dtype=np.uint8)
      opencv_image = cv2.imdecode(file_bytes, 1)
      decoded_objects = decode(opencv_image)
      if decoded_objects:
        for obj in decoded_objects:
          detected_text = obj.data.decode("utf-8")
          st.info(f"دۆزرایەوە لە وێنەدا -> سێریال: **{detected_text}**")
          show_result(detected_text)
      else:
        st.warning("هیچ بارکۆد یان سێریالێک لەم وێنەیەدا نەدۆزرایەوە.")

  elif option == "کامێرای ڕاستەوخۆ":
    st.info("بە ڕێگەی کامێرا وێنەی بارکۆدەکە بگرە:")
    camera_image = st.camera_input("گرتنی وێنە بە کامێرا", key="cam_in")
    if camera_image is not None:
      bytes_data = camera_image.getvalue()
      np_arr = np.frombuffer(
          bytes_data, np.pybytes if hasattr(np, "pybytes") else np.uint8
      )
      img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
      decoded_objects = decode(img)
      if decoded_objects:
        for obj in decoded_objects:
          detected_text = obj.data.decode("utf-8")
          st.write(f"سێریالی سکانکراو: **{detected_text}**")
          show_result(detected_text)
      else:
        st.warning("بارکۆد نەدۆزرایەوە، تکایە ڕووناکی باشتر بەکاربهێنە.")

with tab3:
  st.header("📋 تەواوی خشتەی مەوادە فرۆشراوەکان و دەستکاریکردن")
  try:
    conn = sqlite3.connect("sales_database.db")
    df_all = pd.read_sql_query(
        "SELECT * FROM sold_items ORDER BY date_sold DESC", conn
    )
    conn.close()
    if not df_all.empty:
      st.write(f"کۆی گشتی مەوادە تۆمارکراوەکان: **{len(df_all)}** دانە")
      st.dataframe(df_all, use_container_width=True)
      st.markdown("---")
      st.subheader("دەستکاری یان سڕینەوەی سێریالێک:")
      selected_serial = st.selectbox(
          "سێریالێک هەڵبژێرە بۆ گۆڕین یان سڕینەوە:", df_all["serial_number"]
      )
      col1, col2 = st.columns(2)
      with col1:
        new_val = st.text_input(
            "سێریالی نوێ (ئەگەر دەتەوێت دەستکاری بکەیت):",
            value=selected_serial,
        )
        if st.button("نوێکردنەوەی سێریال"):
          if new_val.strip() != "":
            success = update_serial(selected_serial, new_val.strip())
            if success:
              st.success("✅ سێریالەکە بە سەرکەوتوویی نوێکرایەوە!")
              st.rerun()
            else:
              st.error("⚠️ ئەم سێریالە نوێیە پێشتر بوونی هەیە!")
          else:
            st.warning("تکایە خانەکە بە ڤاڵی بەجێمهێڵە.")
      with col2:
        st.write("سڕینەوەی یەکجارەکی:")
        if st.button("❌ سڕینەوەی ئەم سێریالە", type="primary"):
          delete_serial(selected_serial)
          st.success(f"🗑️ سێریال ({selected_serial}) بە سەرکەوتوویی سڕایەوە!")
          st.rerun()
    else:
      st.info("هیچ مەوادێک لە داتابەیسدا نییە.")
  except Exception as e:
    st.error(f"هەڵە ڕوویدا لە خوێندنەوەی داتابەیس: {e}")
