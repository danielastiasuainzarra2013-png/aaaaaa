import streamlit as st
import sqlite3
import requests

st.set_page_config(page_title="Monitor SAAS Pro", page_icon="📈", layout="centered")

# --- CONFIGURACIÓN ---
WEBHOOK_DISCORD = "https://discord.com/api/webhooks/1519347890185568318/vc7IYgpGxXm3bKI8MS7-D7KfQ_u-Edt2Z9LUWfXyiarZq0Me7GjzMVZlrZ6P7MIYvcXI"
EMAIL_CONTACTO = "astiadaniel19@gmail.com"

# --- FUNCIONES DB ---
def get_db():
    conn = sqlite3.connect("clientes.db", check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, es_premium INTEGER)')
    conn.execute('CREATE TABLE IF NOT EXISTS servicios (id INTEGER PRIMARY KEY, usuario_id INTEGER, url TEXT)')
    return conn

# --- SESIÓN ---
if "usuario_id" not in st.session_state:
    st.session_state.update({"usuario_id": None, "username": None, "es_premium": 0})

conn = get_db()

# --- INTERFAZ ---
if st.session_state.usuario_id is None:
    st.title("📈 Monitor SAAS")
    tab1, tab2 = st.tabs(["🔑 Iniciar Sesión", "📝 Crear Cuenta"])
    with tab1:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                res = conn.execute("SELECT id, username, es_premium FROM usuarios WHERE username=? AND password=?", (u, p)).fetchone()
                if res:
                    st.session_state.update({"usuario_id": res[0], "username": res[1], "es_premium": res[2]})
                    st.rerun()
                else: st.error("Credenciales incorrectas")
    with tab2:
        with st.form("registro"):
            u, p = st.text_input("Nuevo Usuario"), st.text_input("Nueva Contraseña", type="password")
            if st.form_submit_button("Registrarse"):
                try:
                    conn.execute("INSERT INTO usuarios (username, password, es_premium) VALUES (?, ?, 0)", (u, p))
                    conn.commit()
                    st.success("Cuenta creada")
                except: st.error("Usuario ya existe")
else:
    # Sidebar con contacto incluido
    st.sidebar.write(f"👤 **{st.session_state.username}**")
    st.sidebar.write(f"Plan: {'⭐ PREMIUM' if st.session_state.es_premium else '🆓 GRATIS'}")
    
    st.sidebar.markdown("---")
    st.sidebar.write("✉️ **Contacto:**")
    st.sidebar.write(f"[{EMAIL_CONTACTO}](mailto:{EMAIL_CONTACTO})")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.es_premium: st.success("✅ Cuenta Premium activa")
    
    st.title("📈 Panel de Control")
    
    # Obtener servicios
    servicios = conn.execute("SELECT id, url FROM servicios WHERE usuario_id=?", (st.session_state.usuario_id,)).fetchall()
    
    # Lógica de límite (Gratis = max 2)
    if not st.session_state.es_premium and len(servicios) >= 2:
        st.error("⚠️ Límite de 2 webs (Premium: Ilimitado)")
        st.markdown(f"💎 **Bizum 5€**: `600 000 000` | Concepto: `{st.session_state.username}`")
        if st.button("🔔 Notificar pago"):
            requests.post(WEBHOOK_DISCORD, json={"content": f"🚀 Pago pendiente: {st.session_state.username}"})
            st.success("Aviso enviado.")
    else:
        with st.form("add", clear_on_submit=True):
            url = st.text_input("URL (ej: https://google.com)")
            if st.form_submit_button("Añadir"):
                conn.execute("INSERT INTO servicios (usuario_id, url) VALUES (?, ?)", (st.session_state.usuario_id, url))
                conn.commit()
                st.rerun()

    # Listado con estado
    for s in servicios:
        try:
            estado = "🟢 ONLINE" if requests.get(s[1], timeout=3).status_code == 200 else "🔴 CAÍDA"
        except: estado = "🔴 CAÍDA"
        
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.write(f"**{s[1]}**")
        c2.write(estado)
        if c3.button("🗑️", key=f"del_{s[0]}"):
            conn.execute("DELETE FROM servicios WHERE id=?", (s[0],))
            conn.commit()
            st.rerun()

   # Admin - Protegido por usuario y contraseña
    if st.session_state.username == "Dani2008":
        # Verificamos la contraseña directamente de la base de datos
        conn = get_db()
        user_data = conn.execute("SELECT password FROM usuarios WHERE username = ?", ("Dani2008",)).fetchone()
        conn.close()
        
        if user_data and user_data[0] == "200812":
            with st.expander("🛠️ Panel de Administrador"):
                t = st.text_input("Usuario a activar")
                if st.button("✅ Activar Premium"):
                    conn = get_db()
                    conn.execute("UPDATE usuarios SET es_premium=1 WHERE username=?", (t,))
                    conn.commit()
                    conn.close()
                    st.rerun()
                if st.button("💥 RESET DB"):
                    conn = get_db()
                    conn.execute("DELETE FROM usuarios")
                    conn.execute("DELETE FROM servicios")
                    conn.commit()
                    conn.close()
                    st.rerun()
        else:
            st.warning("El administrador no tiene la contraseña configurada correctamente.")
