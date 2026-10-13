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
    page_title="سیستمی فرۆشتن و پشکنینی سێریال", layout="centered"
)

st.title("📦 سیستمی فرۆشتن و پشکنینی سێریال")

tab1, tab2, tab3 = st.tabs(
    ["➕ داخڵکردنی فرۆشتن", "🔍 پشکنین و سکان بە کامێرا", "📋 بەڕێوەبردنی خشتە"]
)

# --- بەشی یەکەم: داخڵکردنی فرۆشتن ---
with tab1:
  st.header("تۆمارکردنی سێریالی فرۆشراو")

  add_method = st.radio(
      "ڕێگەی داخڵکردن هەڵبژێرە:",
      ["نووسینی دەستی", "کامێرای ڕاستەوخۆ (سکان)", "ئەپلۆدکردنی وێنە"],
      key="m1",
  )
  final_serial_add = ""

  if add_method == "نووسینی دەستی":
    final_serial_add = st.text_input("سێریال نەمبێر لێرە بنووسە:", key="t_add")

  elif add_method == "کامێرای ڕاستەوخۆ (سکان)":
    st.info("📷 کامێراکە بەکاربهێنە بۆ گرتنی وێنەی بارکۆدەکە:")
    cam_file = st.camera_input("گرتنی وێنە", key="c_add")
    if cam_file is not None:
      b_data = cam_file.getvalue()
      arr = np.frombuffer(
          b_data, np.pybytes if hasattr(np, "pybytes") else np.uint8
      )
      img_dec = cv2.imdecode(arr, cv2.IMREAD_COLOR)
      decoded_objs = decode(img_dec)
      if decoded_objs:
        final_serial_add = decoded_objs[0].data.decode("utf-8")
        st.success(f"✅ بارکۆد دۆزرایەوە: **{final_serial_add}**")
      else:
        st.warning(
            "⚠️ هیچ بارکۆدێک نەدۆزرایەوە، تکایە ڕووناکی باشتر بکە یان نزیکتر"
            " دەریبکە."
        )

  elif add_method == "ئەپلۆدکردنی وێنە":
    up_file = st.file_uploader(
        "وێنەی بارکۆد هەڵبژێرە...", type=["jpg", "jpeg", "png"], key="u_add"
    )
    if up_file is not None:
      file_bytes = np.asarray(bytearray(up_file.read()), dtype=np.uint8)
      img_dec = cv2.imdecode(file_bytes, 1)
      decoded_objs = decode(img_dec)
      if decoded_objs:
        final_serial_add = decoded_objs[0].data.decode("utf-8")
        st.success(f"✅ بارکۆد دۆزرایەوە: **{final_serial_add}**")
      else:
        st.warning("⚠️ بارکۆد لە وێنەکەدا نەدۆزرایەوە.")

  if st.button("تۆمارکردنی فرۆشتن لە داتابەیس"):
    if final_serial_add and final_serial_add.strip() != "":
      saved = add_serial(final_serial_add.strip())
      if saved:
        st.success(
            f"🎉 سەرکەوتوو بوو! سێریال ({final_serial_add.strip()}) تۆمارکرا."
        )
      else:
        st.warning(f"⚠️ ئاگاداری: ئەم سێریالە پێشتر تۆمار کراوە!")
    else:
      st.error("تکایە سەرەتا سێریال بنووسە یان سکانی بکە.")

  st.subheader("دواین مەوادە تۆمارکراوەکان:")
  try:
    conn = sqlite3.connect("sales_database.db")
    df = pd.read_sql_query(
        "SELECT * FROM sold_items ORDER BY date_sold DESC LIMIT 5", conn
    )
    conn.close()
    if not df.empty:
      st.dataframe(df, use_container_width=True)
    else:
      st.info("هیچ مەوادێک نییە.")
  except:
    pass

# --- بەشی دووەم: پشکنین و سکان بە کامێرا ---
with tab2:
  st.header("🔍 پشکنین و سکانی مەواد")

  check_method = st.radio(
      "ڕێگەی پشکنین هەڵبژێرە:",
      ["نووسینی دەستی", "کامێرای ڕاستەوخۆ (سکان)", "ئەپلۆدکردنی وێنە"],
      key="m2",
  )
  final_serial_check = ""

  def process_check(s_val):
    res = check_serial(s_val)
    if res:
      st.error(
          f"❌ ئەم مەوادە **فرۆشراوە**!\n📅 بەروار و کاتی فرۆشتن:"
          f" **{res[0]}**"
      )
    else:
      st.success(f"✅ ئەم مەوادە **نەفرۆشراوە** (لە مەخزەنە / نوێیە).")

  if check_method == "نووسینی دەستی":
    final_serial_check = st.text_input("سێریال نەمبێر بنووسە بۆ پشکنین:")
    if final_serial_check:
      process_check(final_serial_check.strip())

  elif check_method == "کامێرای ڕاستەوخۆ (سکان)":
    st.info("📷 کامێراکە بەکاربهێنە بۆ پشکنینی بارکۆد:")
    cam_file_c = st.camera_input("پشکنین بە کامێرا", key="c_chk")
    if cam_file_c is not None:
      b_data = cam_file_c.getvalue()
      arr = np.frombuffer(
          b_data, np.pybytes if hasattr(np, "pybytes") else np.uint8
      )
      img_dec = cv2.imdecode(arr, cv2.IMREAD_COLOR)
      decoded_objs = decode(img_dec)
      if decoded_objs:
        final_serial_check = decoded_objs[0].data.decode("utf-8")
        st.write(f"سێریالی سکانکراو: **{final_serial_check}**")
        process_check(final_serial_check)
      else:
        st.warning("⚠️ بارکۆد نەدۆزرایەوە، ڕووناکی باشتر بەکاربهێنە.")

  elif check_method == "ئەپلۆدکردنی وێنە":
    up_file_c = st.file_uploader(
        "وێنەی بارکۆد هەڵبژێرە بۆ پشکنین...",
        type=["jpg", "jpeg", "png"],
        key="u_chk",
    )
    if up_file_c is not None:
      file_bytes = np.asarray(bytearray(up_file_c.read()), dtype=np.uint8)
      img_dec = cv2.imdecode(file_bytes, 1)
      decoded_objs = decode(img_dec)
      if decoded_objs:
        final_serial_check = decoded_objs[0].data.decode("utf-8")
        st.write(f"سێریالی دۆزراوە: **{final_serial_check}**")
        process_check(final_serial_check)
      else:
        st.warning("⚠️ بارکۆد لە وێنەکەدا نەدۆزرایەوە.")

# --- بەشی سێیەم: بەڕێوەبردنی خشتە ---
with tab3:
  st.header("📋 تەواوی خشتە و دەستکاریکردن")
  try:
    conn = sqlite3.connect("sales_database.db")
    df_all = pd.read_sql_query(
        "SELECT * FROM sold_items ORDER BY date_sold DESC", conn
    )
    conn.close()
    if not df_all.empty:
      st.dataframe(df_all, use_container_width=True)

      sel = st.selectbox(
          "سێریالێک هەڵبژێرە بۆ گۆڕین یان سڕینەوە:", df_all["serial_number"]
      )
      col1, col2 = st.columns(2)
      with col1:
        new_v = st.text_input("گۆڕینی سێریال بۆ:", value=sel)
        if st.button("نوێکردنەوە"):
          if update_serial(sel, new_v.strip()):
            st.success("سەرکەوتوو بوو!")
            st.rerun()
          else:
            st.error("هەڵە! ڕەنگە ئەم سێریالە پێشتر هەبێت.")
      with col2:
        if st.button("سڕینەوەی سێریال", type="primary"):
          delete_serial(sel)
          st.success("سڕایەوە!")
          st.rerun()
    else:
      st.info("هیچ داتایەک نییە.")
  except Exception as e:
    st.error(f"هەڵە: {e}")
