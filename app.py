import sqlite3
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


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


st.set_page_config(page_title="سیستمی بارکۆد و سێریال", layout="centered")

st.title("📦 سیستمی فرۆشتن و پشکنینی سێریال")

tab1, tab2, tab3 = st.tabs(
    ["➕ داخڵکردنی فرۆشتن", "🔍 پشکنین و سکان بە کامێرا", "📋 بەڕێوەبردنی خشتە"]
)

# --- بەشی یەکەم: داخڵکردن ---
with tab1:
  st.header("تۆمارکردنی سێریالی فرۆشراو")
  manual_input = st.text_input("سێریال نەمبێر لێرە بنووسە یان سکانی بکە:")

  if st.button("تۆمارکردنی فرۆشتن"):
    if manual_input.strip() != "":
      saved = add_serial(manual_input.strip())
      if saved:
        st.success(
            f"✅ سەرکەوتوو بوو! سێریال ({manual_input.strip()}) تۆمارکرا."
        )
      else:
        st.warning(f"⚠️ ئاگاداری: ئەم سێریالە پێشتر تۆمار کراوە!")
    else:
      st.error("تکایە سێریال بنووسە.")

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

# --- بەشی دووەم: سکان و پشکنینی گەورە و پێشکەوتوو ---
with tab2:
  st.header("🔍 پشکنین و سکانی خێرا بە کامێرا")
  st.write(
      "دەتوانیت سێریال بە دەست بنووسیت یان کامێرای گەورەی خوارەوە بەکاربهێنە:"
  )

  check_manual = st.text_input("پشکنینی دەستی سێریال:")
  if check_manual:
    res = check_serial(check_manual.strip())
    if res:
      st.error(
          f"❌ ئەم مەوادە فرۆشراوە!\n📅 بەروار و کات: **{res[0]}**"
      )
    else:
      st.success(f"✅ ئەم مەوادە نەفرۆشراوە (نوێیە).")

  st.markdown("---")
  st.subheader("📷 سکانەری ڕاستەوخۆی کامێرا (گەورە و ڕوون)")

  # بەکارهێنانی HTML5 Barcode Scanner بۆ ئەوەی کامێرا گەورە بێت و ڕاستەوخۆ بخوێنێتەوە
  scanner_html = """
    <div id="reader" style="width:100%; max-width:500px; margin:auto;"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
        function onScanSuccess(decodedText, decodedResult) {
            console.log(`Code matched = ${decodedText}`, decodedResult);
            // ناردنی سێریالەکە بۆ استریملیت یان نیشاندانی لەسەر شاشە
            let resultDiv = document.getElementById('scan-result');
            resultDiv.innerHTML = "<h3 style='color:green;'>سێریالی دۆزراوە: " + decodedText + "</h3>";
            
            // دروستکردنی لینکی ڕاستەوخۆ بۆ پشکنین
            window.location.href = window.location.origin + window.location.pathname + "?scanned_code=" + encodeURIComponent(decodedText);
        }

        let html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", { fps: 10, qrbox: { width: 250, height: 150 } }, false);
        html5QrcodeScanner.render(onScanSuccess);
    </script>
    <div id="scan-result" style="text-align:center; margin-top:15px;"></div>
    """
  components.html(scanner_html, height=450)

  # پشکنینی ئەو کۆدە لێرە دەکەین کە لە کامێراوە وەرگیراوە
  query_params = st.query_params
  if "scanned_code" in query_params:
    scanned_val = query_params["scanned_code"]
    st.info(f"ئەنجامی سکانی کامێرا بۆ سێریال: **{scanned_val}**")
    res = check_serial(scanned_val)
    if res:
      st.error(
          f"❌ ئاگاداری: ئەم مەوادە **فرۆشراوە**!\n📅 بەروار و کات: `{res[0]}`"
      )
    else:
      st.success(f"✅ ئەم مەوادە **نەفرۆشراوە** (لە مەخزەنە).")

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
            st.error("هەڵە! ڕەنگە ئەم سێریالە هەبێت.")
      with col2:
        if st.button("سڕینەوەی سێریال", type="primary"):
          delete_serial(sel)
          st.success("سڕایەوە!")
          st.rerun()
    else:
      st.info("هیچ داتایەک نییە.")
  except Exception as e:
    st.error(f"هەڵە: {e}")
