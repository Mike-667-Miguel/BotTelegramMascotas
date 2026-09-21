from datetime import datetime
import logging
import math
import requests
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from supabase import create_client, Client

# =============================================================
# CREDENCIALES
# =============================================================
SUPABASE_URL = "https://fhzqxlxbyookevqnfkkf.supabase.co"
SUPABASE_KEY = "sb_publishable_Rt5pXeF66ESD2X7aYkKNPw_mujn5tsl"

# Clave de API de Google con acceso a Geocoding API:
GOOGLE_MAPS_API_KEY = "AIzaSyDJzWJ63Cg099WErTVRMKS79mpPhlT7-tI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Estados para la conversación de creación (0 a 16)
(
    NOMBRE,
    DESCRIPCION,
    REPORTE_NOMBRE,
    REPORTE_TELEFONO,
    CALLE,
    REFERENCIAS,
    COLONIA,
    CODIGO_POSTAL,
    TIPO_REPORTE,
    RESGUARDO,
    RAZA,
    TAMANO,
    CARACTERISTICAS,
    COLLAR,
    COLOR,
    SEXO,
    FOTO,
) = range(17)

# Estados para la conversación de edición y eliminación (17 a 20)
ELEGIR_REPORTE, ELEGIR_CAMPO, PEDIR_VALOR, EDIT_RESGUARDO = range(17, 21)


# =============================================================
# FUNCIONES AUXILIARES: GOOGLE MAPS Y CÁLCULO DE DISTANCIA
# =============================================================

def obtener_coordenadas(calle, colonia, codigo_postal):
    """Convierte la dirección enviada por el usuario en coordenadas GPS vía Google Maps API."""
    direccion_completa = f"{calle}, {colonia}, CP {codigo_postal}, San Luis Potosi, Mexico"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(direccion_completa)}&key={GOOGLE_MAPS_API_KEY}"

    try:
        response = requests.get(url)
        res = response.json()
        print("\n--- RESPUESTA DE GOOGLE MAPS ---")
        print(f"Status: {res.get('status')}")

        if res.get("status") == "OK":
            location = res["results"][0]["geometry"]["location"]
            print(f"Coordenadas encontradas: Lat {location['lat']}, Lng {location['lng']}")
            return location["lat"], location["lng"]
        else:
            print(f"Mensaje de error: {res.get('error_message', 'Sin mensaje de error')}")

    except Exception as e:
        print(f"Error al geolocalizar con Google Maps: {e}")
    return None, None


def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula la distancia en kilómetros entre dos coordenadas GPS usando la fórmula de Haversine."""
    R = 6371.0  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def obtener_refugio_mas_cercano(lat_reporte, lon_reporte):
    """Consulta la tabla 'refugios' en Supabase y devuelve el más próximo a las coordenadas del reporte."""
    res_refugios = supabase.table("refugios").select("*").execute()
    
    print(f"\n[DEBUG SUPABASE] Registros encontrados: {len(res_refugios.data) if res_refugios.data else 0}")
    if not res_refugios.data:
        return None, None

    refugio_cercano = None
    distancia_minima = float("inf")

    for ref in res_refugios.data:
        lat_ref = ref.get("latitud")
        lon_ref = ref.get("longitud")

        if lat_ref is not None and lon_ref is not None:
            dist = calcular_distancia(
                float(lat_reporte),
                float(lon_reporte),
                float(lat_ref),
                float(lon_ref),
            )
            print(f"[DEBUG DISTANCIA] Refugio en '{ref.get('direccion', 'N/A')}' a {dist:.2f} km")
            if dist < distancia_minima:
                distancia_minima = dist
                refugio_cercano = ref

    return refugio_cercano, distancia_minima


# ---------------------------------------------------------
# 1. Flujo de creación de reporte
# ---------------------------------------------------------

async def start_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "<b>Nuevo Reporte</b>\nPor favor, escribe el nombre o título del reporte:",
        parse_mode="HTML"
    )
    return NOMBRE


async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["titulo"] = update.message.text
    await update.message.reply_text("Escribe la descripción detallada del problema o reporte:")
    return DESCRIPCION


async def recibir_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["descripcion"] = update.message.text
    await update.message.reply_text("Nombre de quien realiza el reporte:")
    return REPORTE_NOMBRE


async def recibir_reporte_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["reporte_nombre"] = update.message.text
    await update.message.reply_text("Número de teléfono de quien realiza el reporte:")
    return REPORTE_TELEFONO


async def recibir_reporte_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["reporte_telefono"] = update.message.text
    await update.message.reply_text("Calle donde se encontró o perdió a la mascota:")
    return CALLE


async def recibir_calle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["calle"] = update.message.text
    await update.message.reply_text("Referencias del lugar:")
    return REFERENCIAS


async def recibir_referencias(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["referencias"] = update.message.text
    await update.message.reply_text("Colonia:")
    return COLONIA


async def recibir_colonia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["colonia"] = update.message.text
    await update.message.reply_text("Código postal del lugar del reporte:")
    return CODIGO_POSTAL


async def recibir_codigo_postal_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["codigo_postal"] = update.message.text
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Extravío de mascota", callback_data="tipo_extravio"),
            InlineKeyboardButton("Encontré una mascota", callback_data="tipo_encontrado")
        ]
    ])
    await update.message.reply_text("Selecciona el tipo de reporte:", reply_markup=keyboard)
    return TIPO_REPORTE


async def recibir_tipo_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    seleccion = query.data
    tipo_str = "Encontre una mascota" if seleccion == "tipo_encontrado" else "Extravio de mascota"
    context.user_data["tipo_reporte"] = tipo_str

    if seleccion == "tipo_encontrado":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Domicilio", callback_data="resguardo_domicilio"),
                InlineKeyboardButton("En refugio", callback_data="resguardo_refugio")
            ]
        ])
        await query.edit_message_text("Indica el resguardo actual de la mascota:", reply_markup=keyboard)
        return RESGUARDO
    else:
        context.user_data["resguardo"] = None
        await query.edit_message_text("Raza del animalito (o lo más aproximado):")
        return RAZA


async def recibir_resguardo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    seleccion = query.data
    if seleccion == "resguardo_refugio":
        context.user_data["resguardo"] = "refugio"
        await query.edit_message_text("Has seleccionado resguardo en Refugio.")
    else:
        context.user_data["resguardo"] = "domicilio"
        await query.edit_message_text("Has seleccionado resguardo en Domicilio.")

    await query.message.reply_text("Raza del animalito (o lo más aproximado):")
    return RAZA


async def recibir_raza(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["raza"] = update.message.text
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Pequeño", callback_data="tam_pequeno"),
            InlineKeyboardButton("Mediano", callback_data="tam_mediano"),
            InlineKeyboardButton("Grande", callback_data="tam_grande")
        ]
    ])
    await update.message.reply_text("Selecciona el tamaño:", reply_markup=keyboard)
    return TAMANO


async def recibir_tamano(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    materia_map = {
        "tam_pequeno": "Pequeno",
        "tam_mediano": "Mediano",
        "tam_grande": "Grande"
    }
    context.user_data["tamano"] = materia_map.get(query.data, "Desconocido")
    
    await query.edit_message_text("Escribe las características distintivas del animalito:")
    return CARACTERISTICAS


async def recibir_caracteristicas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["caracteristicas"] = update.message.text
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Sí", callback_data="collar_si"),
            InlineKeyboardButton("No", callback_data="collar_no")
        ]
    ])
    await update.message.reply_text("¿Cuenta con collar?", reply_markup=keyboard)
    return COLLAR


async def recibir_collar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data["collar"] = "Si" if query.data == "collar_si" else "No"
    await query.edit_message_text("Color principal del animalito:")
    return COLOR


async def recibir_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["color"] = update.message.text
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Macho", callback_data="sexo_macho"),
            InlineKeyboardButton("Hembra", callback_data="sexo_hembra")
        ]
    ])
    await update.message.reply_text("Selecciona el sexo:", reply_markup=keyboard)
    return SEXO


async def recibir_sexo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data["sexo"] = "Macho" if query.data == "sexo_macho" else "Hembra"
    await query.edit_message_text("Por favor, envía una foto de la mascota como imagen:")
    return FOTO


async def recibir_foto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    telegram_id = str(update.message.from_user.id)
    foto_id = None
    foto_url_publica = None

    if update.message.photo:
        foto_id = update.message.photo[-1].file_id

        try:
            foto_file = await update.message.photo[-1].get_file()
            foto_bytes = await foto_file.download_as_bytearray()
            nombre_archivo = f"mascota_{telegram_id}_{int(datetime.now().timestamp())}.jpg"

            supabase.storage.from_("mascotas").upload(
                path=nombre_archivo,
                file=bytes(foto_bytes),
                file_options={"content-type": "image/jpeg"},
            )

            foto_url_publica = supabase.storage.from_("mascotas").get_public_url(nombre_archivo)

        except Exception as err_storage:
            print(f"Advertencia al subir foto a Storage: {err_storage}")

    tiene_collar_bool = context.user_data.get("collar") == "Si"

    # --- Geolocalización y Búsqueda del Refugio Más Cercano ---
    calle_usr = context.user_data.get("calle", "")
    colonia_usr = context.user_data.get("colonia", "")
    cp_usr = context.user_data.get("codigo_postal", "")
    resguardo_usr = str(context.user_data.get("resguardo", "")).lower().strip()

    id_refugio_encontrado = None
    texto_refugio = ""
    link_mapa = None

    if "refugio" in resguardo_usr:
        print("[DEBUG] Entrando a consultar Google Maps API...")
        lat, lng = obtener_coordenadas(calle_usr, colonia_usr, cp_usr)

        if lat and lng:
            refugio, distancia = obtener_refugio_mas_cercano(lat, lng)
            if refugio:
                id_refugio_encontrado = refugio.get("id_refugio") or refugio.get("id")
                
                # Obtenemos el enlace almacenado en la columna enlace_de_mapa o lo armamos por GPS
                link_mapa = refugio.get("enlace_de_mapa") or f"https://www.google.com/maps/search/?api=1&query={refugio['latitud']},{refugio['longitud']}"

                texto_refugio = (
                    f"\n\n <b>De acuerdo a tu ubicación, este es el refugio más cercano:</b>\n\n"
                    f" <b>Dirección:</b> {refugio.get('direccion', 'N/A')}\n"
                    f" <b>C.P.:</b> {refugio.get('codigo_postal', 'N/A')}\n"
                    f" <b>Distancia aprox:</b> {distancia:.2f} km\n"
                    f" <a href='{link_mapa}'>Abrir ubicación en Google Maps</a>"
                )
                print(f"[DEBUG] Refugio más cercano a {distancia:.2f} km")
            else:
                print("[DEBUG] No se encontraron refugios en la base de datos.")
        else:
            print("[DEBUG] No se pudieron obtener coordenadas de Google Maps.")

    try:
        usr_check = (
            supabase.table("usuarios")
            .select("id_usuario")
            .eq("telegram_id", telegram_id)
            .execute()
        )

        if usr_check.data and len(usr_check.data) > 0:
            id_usuario = usr_check.data[0]["id_usuario"]
            supabase.table("usuarios").update(
                {
                    "nombre": context.user_data.get("reporte_nombre"),
                    "telefono": context.user_data.get("reporte_telefono"),
                }
            ).eq("id_usuario", id_usuario).execute()
        else:
            datos_usuario = {
                "nombre": context.user_data.get("reporte_nombre"),
                "telegram_id": telegram_id,
                "telefono": context.user_data.get("reporte_telefono"),
            }
            res_usr = supabase.table("usuarios").insert(datos_usuario).execute()
            id_usuario = res_usr.data[0]["id_usuario"]

        datos_mascota = {
            "raza": context.user_data.get("raza"),
            "tamano": context.user_data.get("tamano"),
            "caracteristicas": context.user_data.get("caracteristicas"),
            "tiene_collar": tiene_collar_bool,
            "color": context.user_data.get("color"),
            "sexo": context.user_data.get("sexo"),
            "foto_url": foto_url_publica or foto_id,
        }
        res_mascota = supabase.table("mascotas").insert(datos_mascota).execute()
        id_mascota = res_mascota.data[0]["id_mascota"]

        datos_reporte = {
            "id_usuario": id_usuario,
            "id_mascota": id_mascota,
            "id_refugio": id_refugio_encontrado,
            "fecha_de_reporte": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "calle": calle_usr,
            "referencia": context.user_data.get("referencias"),
            "colonia": colonia_usr,
            "tipo_de_reporte": context.user_data.get("tipo_reporte"),
            "codigo_postal": cp_usr,
            "estatus_resguardo": context.user_data.get("resguardo"),
            "nombre_refugio": context.user_data.get("nombre_refugio"),
            "titulo": context.user_data.get("titulo"),
            "descripcion": context.user_data.get("descripcion"),
        }
        supabase.table("reportes").insert(datos_reporte).execute()

        await update.message.reply_text("Reporte e imagen guardados exitosamente en la base de datos.")

    except Exception as e:
        print(f"Error al guardar en las tablas de Supabase: {e}")
        await update.message.reply_text("Hubo un error al guardar el reporte en la base de datos.")
        context.user_data.clear()
        return ConversationHandler.END

    resumen = (
        "<b>Este es tu reporte realizado:</b>\n\n"
        f"<b>Título:</b> {context.user_data.get('titulo')}\n"
        f"<b>Descripción:</b> {context.user_data.get('descripcion')}\n"
        f"<b>Reporta:</b> {context.user_data.get('reporte_nombre')}\n"
        f"<b>Teléfono:</b> {context.user_data.get('reporte_telefono')}\n"
        f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"<b>Calle:</b> {calle_usr}\n"
        f"<b>Referencias:</b> {context.user_data.get('referencias')}\n"
        f"<b>Colonia:</b> {colonia_usr}\n"
        f"<b>C.P.:</b> {cp_usr}\n"
        f"<b>Tipo:</b> {context.user_data.get('tipo_reporte')}\n"
        f"<b>Resguardo:</b> {context.user_data.get('resguardo', 'N/A')}\n"
        f"<b>Raza:</b> {context.user_data.get('raza')}\n"
        f"<b>Tamaño:</b> {context.user_data.get('tamano')}\n"
        f"<b>Características:</b> {context.user_data.get('caracteristicas')}\n"
        f"<b>Collar:</b> {context.user_data.get('collar')}\n"
        f"<b>Color:</b> {context.user_data.get('color')}\n"
        f"<b>Sexo:</b> {context.user_data.get('sexo')}"
        f"{texto_refugio}"
    )

    # Botón dinámico interactivo de Telegram
    reply_markup_final = None
    if link_mapa:
        reply_markup_final = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗺️ Ver refugio en Google Maps", url=link_mapa)]
        ])

    if update.message.photo:
        await update.message.reply_photo(
            photo=foto_id, 
            caption=resumen, 
            parse_mode="HTML",
            reply_markup=reply_markup_final
        )
    else:
        await update.message.reply_text(
            resumen, 
            parse_mode="HTML",
            reply_markup=reply_markup_final
        )

    context.user_data.clear()
    return ConversationHandler.END


# ---------------------------------------------------------
# 2. Flujo de edición adaptativo
# ---------------------------------------------------------

async def mis_reportes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    telegram_id = str(update.message.from_user.id)

    try:
        usr_res = (
            supabase.table("usuarios")
            .select("id_usuario")
            .eq("telegram_id", telegram_id)
            .execute()
        )

        if not usr_res.data:
            await update.message.reply_text("Aún no has registrado ningún reporte.")
            return ConversationHandler.END

        id_usuario = usr_res.data[0]["id_usuario"]

        reportes_res = (
            supabase.table("reportes")
            .select("id_reporte, id_mascota, tipo_de_reporte, estatus_resguardo, calle, referencia, colonia, codigo_postal, fecha_de_reporte, mascotas(raza, tamano, color, caracteristicas, tiene_collar, sexo, foto_url)")
            .eq("id_usuario", id_usuario)
            .execute()
        )

        if not reportes_res.data:
            await update.message.reply_text("No tienes reportes guardados.")
            return ConversationHandler.END

        await update.message.reply_text("<b>Tus Reportes Registrados:</b>", parse_mode="HTML")

        for r in reportes_res.data:
            mascota = r.get("mascotas", {}) or {}
            collar_txt = "Sí" if mascota.get("tiene_collar") else "No"
            
            texto = (
                f"<b>Reporte #{r['id_reporte']}</b>\n"
                f"<b>Tipo:</b> {r.get('tipo_de_reporte')}\n"
                f"<b>Resguardo:</b> {r.get('estatus_resguardo', 'N/A')}\n"
                f"<b>Ubicación:</b> {r.get('calle')}, Col. {r.get('colonia')}, C.P. {r.get('codigo_postal')}\n"
                f"<b>Referencia:</b> {r.get('referencia', 'N/A')}\n"
                f"<b>Raza:</b> {mascota.get('raza', 'N/A')}\n"
                f"<b>Tamaño:</b> {mascota.get('tamano', 'N/A')}\n"
                f"<b>Color:</b> {mascota.get('color', 'N/A')}\n"
                f"<b>Collar:</b> {collar_txt}\n"
                f"<b>Sexo:</b> {mascota.get('sexo', 'N/A')}\n"
                f"<b>Características:</b> {mascota.get('caracteristicas', 'N/A')}\n"
                f"<b>Fecha:</b> {r.get('fecha_de_reporte')}"
            )

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Editar", callback_data=f"edit:{r['id_reporte']}:{r['id_mascota']}"),
                    InlineKeyboardButton("Eliminar", callback_data=f"del:{r['id_reporte']}:{r['id_mascota']}")
                ]
            ])

            await update.message.reply_text(texto, reply_markup=keyboard, parse_mode="HTML")

        return ELEGIR_REPORTE

    except Exception as e:
        print(f"Error al obtener reportes: {e}")
        await update.message.reply_text("Ocurrió un error al consultar tus reportes.")
        return ConversationHandler.END


async def eliminar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    partes = query.data.split(":")
    id_reporte = partes[1]
    id_mascota = partes[2]

    try:
        id_rep_val = int(id_reporte) if str(id_reporte).isdigit() else id_reporte
        id_mas_val = int(id_mascota) if str(id_mascota).isdigit() else id_mascota

        supabase.table("reportes").delete().eq("id_reporte", id_rep_val).execute()

        if id_mas_val:
            supabase.table("mascotas").delete().eq("id_mascota", id_mas_val).execute()

        await query.edit_message_text(
            f"El <b>Reporte #{id_reporte}</b> ha sido eliminado correctamente.",
            parse_mode="HTML"
        )

    except Exception as e:
        print(f"Error al eliminar reporte en DB: {e}")
        await query.edit_message_text("Ocurrió un error al intentar eliminar el reporte.")

    context.user_data.clear()
    return ConversationHandler.END


async def seleccionar_campo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    partes = query.data.split(":")
    id_reporte = partes[1]
    id_mascota = partes[2]

    context.user_data["edit_id_reporte"] = id_reporte
    context.user_data["edit_id_mascota"] = id_mascota

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Calle", callback_data="campo_calle"), InlineKeyboardButton("Colonia", callback_data="campo_colonia")],
        [InlineKeyboardButton("Referencia", callback_data="campo_referencia"), InlineKeyboardButton("Código Postal", callback_data="campo_codigo_postal")],
        [InlineKeyboardButton("Tipo Reporte", callback_data="campo_tipo_de_reporte"), InlineKeyboardButton("Resguardo", callback_data="campo_estatus_resguardo")],
        [InlineKeyboardButton("Raza", callback_data="campo_raza"), InlineKeyboardButton("Tamaño", callback_data="campo_tamano")],
        [InlineKeyboardButton("Color", callback_data="campo_color"), InlineKeyboardButton("Características", callback_data="campo_caracteristicas")],
        [InlineKeyboardButton("Tiene Collar", callback_data="campo_tiene_collar"), InlineKeyboardButton("Sexo", callback_data="campo_sexo")],
        [InlineKeyboardButton("Nueva Foto", callback_data="campo_foto")]
    ])

    await query.edit_message_text(
        f"Selecciona el campo que deseas modificar del <b>Reporte #{id_reporte}</b>:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    return ELEGIR_CAMPO


async def pedir_nuevo_valor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    campo = query.data.replace("campo_", "")
    context.user_data["edit_campo"] = campo

    if campo == "tipo_de_reporte":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Extravío de mascota", callback_data="val:Extravio de mascota")],
            [InlineKeyboardButton("Encontré una mascota", callback_data="val:Encontre una mascota")]
        ])
        await query.edit_message_text("Selecciona el nuevo <b>tipo de reporte</b>:", reply_markup=keyboard, parse_mode="HTML")
        return PEDIR_VALOR

    elif campo == "estatus_resguardo":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Domicilio", callback_data="val:domicilio")],
            [InlineKeyboardButton("Refugio", callback_data="val:refugio")]
        ])
        await query.edit_message_text("Selecciona el nuevo <b>estatus de resguardo</b>:", reply_markup=keyboard, parse_mode="HTML")
        return PEDIR_VALOR

    elif campo == "tiene_collar":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Sí", callback_data="val:True")],
            [InlineKeyboardButton("No", callback_data="val:False")]
        ])
        await query.edit_message_text("¿Cuenta con <b>collar</b>?:", reply_markup=keyboard, parse_mode="HTML")
        return PEDIR_VALOR

    elif campo == "sexo":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Macho", callback_data="val:Macho")],
            [InlineKeyboardButton("Hembra", callback_data="val:Hembra")]
        ])
        await query.edit_message_text("Selecciona el <b>sexo</b>:", reply_markup=keyboard, parse_mode="HTML")
        return PEDIR_VALOR

    elif campo == "tamano":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Pequeño", callback_data="val:Pequeno")],
            [InlineKeyboardButton("Mediano", callback_data="val:Mediano")],
            [InlineKeyboardButton("Grande", callback_data="val:Grande")]
        ])
        await query.edit_message_text("Selecciona el nuevo <b>tamaño</b>:", reply_markup=keyboard, parse_mode="HTML")
        return PEDIR_VALOR

    instrucciones = {
        "calle": "Escribe la nueva <b>calle</b>:",
        "colonia": "Escribe la nueva <b>colonia</b>:",
        "referencia": "Escribe la nueva <b>referencia</b> del lugar:",
        "codigo_postal": "Escribe el nuevo <b>código postal</b>:",
        "raza": "Escribe la nueva <b>raza</b>:",
        "color": "Escribe el nuevo <b>color</b>:",
        "caracteristicas": "Escribe las nuevas <b>características</b>:",
        "foto": "Por favor, envía la <b>nueva foto</b> de la mascota como una imagen:"
    }

    await query.edit_message_text(
        instrucciones.get(campo, f"Escribe el nuevo valor para {campo}:"),
        parse_mode="HTML"
    )
    return PEDIR_VALOR


async def guardar_modificacion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    campo = context.user_data.get("edit_campo")
    id_reporte = context.user_data.get("edit_id_reporte")
    id_mascota = context.user_data.get("edit_id_mascota")
    telegram_id = str(update.effective_user.id)

    id_rep_val = int(id_reporte) if str(id_reporte).isdigit() else id_reporte
    id_mas_val = int(id_mascota) if str(id_mascota).isdigit() else id_mascota

    nuevo_valor = None

    if update.callback_query:
        query = update.callback_query
        await query.answer()

        nuevo_valor = query.data.replace("val:", "")

        if campo == "tipo_de_reporte":
            if nuevo_valor == "Encontre una mascota":
                supabase.table("reportes").update({"tipo_de_reporte": nuevo_valor}).eq("id_reporte", id_rep_val).execute()
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Domicilio", callback_data="edit_resg:domicilio")],
                    [InlineKeyboardButton("Refugio", callback_data="edit_resg:refugio")]
                ])
                await query.edit_message_text("El tipo cambió a 'Encontré una mascota'. Indica dónde se encuentra resguardada:", reply_markup=keyboard)
                return EDIT_RESGUARDO
            else:
                supabase.table("reportes").update({
                    "tipo_de_reporte": nuevo_valor,
                    "estatus_resguardo": None,
                    "nombre_refugio": None
                }).eq("id_reporte", id_rep_val).execute()

                await query.edit_message_text("Reporte actualizado a <b>Extravío de mascota</b>.", parse_mode="HTML")
                context.user_data.clear()
                return ConversationHandler.END

        elif campo == "estatus_resguardo":
            supabase.table("reportes").update({
                "estatus_resguardo": nuevo_valor,
                "nombre_refugio": None
            }).eq("id_reporte", id_rep_val).execute()

            await query.edit_message_text(f"Resguardo actualizado a <b>{nuevo_valor.capitalize()}</b>.", parse_mode="HTML")
            context.user_data.clear()
            return ConversationHandler.END

        elif campo == "tiene_collar":
            nuevo_valor = True if nuevo_valor == "True" else False

    elif campo == "foto":
        if not update.message or not update.message.photo:
            await update.message.reply_text("No enviaste una imagen válida. Operación cancelada.")
            context.user_data.clear()
            return ConversationHandler.END

        try:
            foto_file = await update.message.photo[-1].get_file()
            foto_bytes = await foto_file.download_as_bytearray()
            nombre_archivo = f"mascota_{telegram_id}_{int(datetime.now().timestamp())}.jpg"

            supabase.storage.from_("mascotas").upload(
                path=nombre_archivo,
                file=bytes(foto_bytes),
                file_options={"content-type": "image/jpeg"},
            )

            nuevo_valor = supabase.storage.from_("mascotas").get_public_url(nombre_archivo)
            campo = "foto_url"
        except Exception as err:
            print(f"Error al subir nueva imagen: {err}")
            await update.message.reply_text("Error al procesar la imagen.")
            context.user_data.clear()
            return ConversationHandler.END
    else:
        if not update.message or not update.message.text:
            await update.message.reply_text("Debes responder con un texto válido. Operación cancelada.")
            context.user_data.clear()
            return ConversationHandler.END
        nuevo_valor = update.message.text

    try:
        if campo in ["calle", "colonia", "referencia", "codigo_postal"]:
            supabase.table("reportes").update({campo: nuevo_valor}).eq("id_reporte", id_rep_val).execute()
        elif campo in ["raza", "tamano", "color", "caracteristicas", "tiene_collar", "sexo", "foto_url"]:
            supabase.table("mascotas").update({campo: nuevo_valor}).eq("id_mascota", id_mas_val).execute()

        msg_exito = f"El campo <b>{campo}</b> ha sido actualizado correctamente."
        if update.callback_query:
            await update.callback_query.edit_message_text(msg_exito, parse_mode="HTML")
        else:
            await update.message.reply_text(msg_exito, parse_mode="HTML")

    except Exception as e:
        print(f"Error al actualizar reporte en DB: {e}")
        error_msg = "Ocurrió un error al guardar los cambios en la base de datos."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)

    context.user_data.clear()
    return ConversationHandler.END


async def edit_procesar_resguardo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    resguardo = query.data.replace("edit_resg:", "")
    id_reporte = context.user_data.get("edit_id_reporte")
    id_rep_val = int(id_reporte) if str(id_reporte).isdigit() else id_reporte

    supabase.table("reportes").update({
        "estatus_resguardo": resguardo,
        "nombre_refugio": None
    }).eq("id_reporte", id_rep_val).execute()

    await query.edit_message_text(f"Reporte actualizado a <b>Encontré una mascota ({resguardo.capitalize()})</b>.", parse_mode="HTML")
    context.user_data.clear()
    return ConversationHandler.END


# ---------------------------------------------------------
# 3. Cancelación y configuración del bot
# ---------------------------------------------------------

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Operación cancelada.", reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END


def main():
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0
    )

    app = (
        ApplicationBuilder()
        .token("8691909785:AAFQC2Ir62_MqxHYOvcGXM3k2JkCgGInuqc")
        .request(request)
        .build()
    )

    conv_handler_crear = ConversationHandler(
        entry_points=[
            CommandHandler("reporte", start_reporte),
            CommandHandler("reportar", start_reporte),
        ],
        states={
            NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            DESCRIPCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_descripcion)],
            REPORTE_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_reporte_nombre)],
            REPORTE_TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_reporte_telefono)],
            CALLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_calle)],
            REFERENCIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_referencias)],
            COLONIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_colonia)],
            CODIGO_POSTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_codigo_postal_msg)],
            TIPO_REPORTE: [CallbackQueryHandler(recibir_tipo_reporte, pattern="^tipo_")],
            RESGUARDO: [CallbackQueryHandler(recibir_resguardo, pattern="^resguardo_")],
            RAZA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_raza)],
            TAMANO: [CallbackQueryHandler(recibir_tamano, pattern="^tam_")],
            CARACTERISTICAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_caracteristicas)],
            COLLAR: [CallbackQueryHandler(recibir_collar, pattern="^collar_")],
            COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_color)],
            SEXO: [CallbackQueryHandler(recibir_sexo, pattern="^sexo_")],
            FOTO: [MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, recibir_foto)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )

    conv_handler_editar = ConversationHandler(
        entry_points=[
            CommandHandler("mis_reportes", mis_reportes)
        ],
        states={
            ELEGIR_REPORTE: [
                CallbackQueryHandler(seleccionar_campo, pattern="^edit:"),
                CallbackQueryHandler(eliminar_reporte, pattern="^del:")
            ],
            ELEGIR_CAMPO: [CallbackQueryHandler(pedir_nuevo_valor, pattern="^campo_")],
            PEDIR_VALOR: [
                CallbackQueryHandler(guardar_modificacion, pattern="^val:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_modificacion),
                MessageHandler(filters.PHOTO, guardar_modificacion)
            ],
            EDIT_RESGUARDO: [CallbackQueryHandler(edit_procesar_resguardo, pattern="^edit_resg:")]
        },
        fallbacks=[CommandHandler("cancelar", cancel)]
    )

    app.add_handler(conv_handler_crear)
    app.add_handler(conv_handler_editar)

    print("Bot activo con integración de refugios y Google Maps...")
    app.run_polling()


if __name__ == "__main__":
    main()