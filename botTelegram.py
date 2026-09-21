from datetime import datetime
import logging
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
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

# Configuración de Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# =============================================================
# CREDENCIALES DE SUPABASE Y BOT
# =============================================================
SUPABASE_URL = "https://fhzqxlxbyookevqnfkkf.supabase.co"
SUPABASE_KEY = "sb_publishable_Rt5pXeF66ESD2X7aYkKNPw_mujn5tsl"
TELEGRAM_TOKEN = "8691909785:AAEV7e6UEH0wQmpgXP5ixhX6GmJKpKWXe7g"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =============================================================
# ESTADOS DE CONVERSACIÓN
# =============================================================
# Crear reporte
(
    NOMBRE,
    DESCRIPCION,
    REPORTE_NOMBRE,
    REPORTE_TELEFONO,
    CALLE,
    REFERENCIAS,
    COLONIA,
    TIPO_REPORTE,
    CODIGO_POSTAL,
    RAZA,
    TAMANO,
    CARACTERISTICAS,
    COLLAR,
    COLOR,
    SEXO,
    FOTO,
) = range(16)

# Editar/Eliminar reporte
ELEGIR_REPORTE, ELEGIR_CAMPO, PEDIR_VALOR = range(16, 19)


# =============================================================
# 1. FLUJO DE CREACIÓN DE REPORTE
# =============================================================

async def start_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "<b>Nuevo Reporte</b>\nPor favor, escribe el título de tu reporte:",
        parse_mode="HTML"
    )
    return NOMBRE


async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["titulo"] = update.message.text
    await update.message.reply_text("Escribe la descripción detallada del problema/reporte:")
    return DESCRIPCION


async def recibir_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["descripcion"] = update.message.text
    await update.message.reply_text("Nombre completo de quien realiza el reporte:")
    return REPORTE_NOMBRE


async def recibir_reporte_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["reporte_nombre"] = update.message.text
    await update.message.reply_text("Número de teléfono de contacto:")
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
    await update.message.reply_text("Tipo de reporte (Extravío de mascota / Encontré una mascota):")
    return TIPO_REPORTE


async def recibir_tipo_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["tipo_reporte"] = update.message.text
    await update.message.reply_text("Código Postal:")
    return CODIGO_POSTAL


async def recibir_codigo_postal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["codigo_postal"] = update.message.text
    await update.message.reply_text("Raza del animalito (o aproximada):")
    return RAZA


async def recibir_raza(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["raza"] = update.message.text
    await update.message.reply_text("Tamaño (Pequeño, Mediano, Grande):")
    return TAMANO


async def recibir_tamano(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["tamano"] = update.message.text
    await update.message.reply_text("Características específicas del animalito:")
    return CARACTERISTICAS


async def recibir_caracteristicas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["caracteristicas"] = update.message.text
    await update.message.reply_text("¿Cuenta con collar? (si / no):")
    return COLLAR


async def recibir_collar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["collar"] = update.message.text
    await update.message.reply_text("Color principal:")
    return COLOR


async def recibir_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["color"] = update.message.text
    await update.message.reply_text("Sexo (Macho / Hembra):")
    return SEXO


async def recibir_sexo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["sexo"] = update.message.text
    await update.message.reply_text("Por favor, envía una foto de la mascota:")
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

            # Subir imagen a Supabase Storage
            supabase.storage.from_("mascotas").upload(
                path=nombre_archivo,
                file=bytes(foto_bytes),
                file_options={"content-type": "image/jpeg"},
            )

            foto_url_publica = supabase.storage.from_("mascotas").get_public_url(nombre_archivo)
        except Exception as err_storage:
            print(f"Advertencia al subir foto a Storage: {err_storage}")

    respuesta_collar = context.user_data.get("collar", "").strip().lower()
    tiene_collar_bool = respuesta_collar in ["si", "sí", "yes", "true"]

    try:
        # 1. Registrar/Actualizar Usuario
        usr_check = (
            supabase.table("usuarios")
            .select("id_usuario")
            .eq("telegram_id", telegram_id)
            .execute()
        )

        if usr_check.data and len(usr_check.data) > 0:
            id_usuario = usr_check.data[0]["id_usuario"]
            supabase.table("usuarios").update({
                "nombre": context.user_data.get("reporte_nombre"),
                "telefono": context.user_data.get("reporte_telefono"),
            }).eq("id_usuario", id_usuario).execute()
        else:
            res_usr = supabase.table("usuarios").insert({
                "nombre": context.user_data.get("reporte_nombre"),
                "telegram_id": telegram_id,
                "telefono": context.user_data.get("reporte_telefono"),
            }).execute()
            id_usuario = res_usr.data[0]["id_usuario"]

        # 2. Insertar Mascota
        res_mascota = supabase.table("mascotas").insert({
            "raza": context.user_data.get("raza"),
            "tamano": context.user_data.get("tamano"),
            "caracteristicas": context.user_data.get("caracteristicas"),
            "tiene_collar": tiene_collar_bool,
            "color": context.user_data.get("color"),
            "sexo": context.user_data.get("sexo"),
            "foto_url": foto_url_publica or foto_id,
        }).execute()
        id_mascota = res_mascota.data[0]["id_mascota"]

        # 3. Insertar Reporte
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        supabase.table("reportes").insert({
            "id_usuario": id_usuario,
            "id_mascota": id_mascota,
            "fecha_de_reporte": fecha_actual,
            "calle": context.user_data.get("calle"),
            "referencia": context.user_data.get("referencias"),
            "colonia": context.user_data.get("colonia"),
            "tipo_de_reporte": context.user_data.get("tipo_reporte"),
            "codigo_postal": context.user_data.get("codigo_postal"),
        }).execute()

        await update.message.reply_text("✅ ¡Reporte e imagen guardados con éxito en la base de datos!")

    except Exception as e:
        print(f"Error al guardar en Supabase: {e}")
        await update.message.reply_text("❌ Hubo un error al guardar el reporte en la base de datos.")

    # Resumen HTML
    resumen = (
        "<b>Resumen de tu Reporte:</b>\n\n"
        f"<b>Título:</b> {context.user_data.get('titulo')}\n"
        f"<b>Descripción:</b> {context.user_data.get('descripcion')}\n"
        f"<b>Reporta:</b> {context.user_data.get('reporte_nombre')}\n"
        f"<b>Teléfono:</b> {context.user_data.get('reporte_telefono')}\n"
        f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"<b>Calle:</b> {context.user_data.get('calle')}\n"
        f"<b>Referencias:</b> {context.user_data.get('referencias')}\n"
        f"<b>Colonia:</b> {context.user_data.get('colonia')}\n"
        f"<b>Tipo:</b> {context.user_data.get('tipo_reporte')}\n"
        f"<b>C.P.:</b> {context.user_data.get('codigo_postal')}\n"
        f"<b>Raza:</b> {context.user_data.get('raza')}\n"
        f"<b>Tamaño:</b> {context.user_data.get('tamano')}\n"
        f"<b>Características:</b> {context.user_data.get('caracteristicas')}\n"
        f"<b>Collar:</b> {context.user_data.get('collar')}\n"
        f"<b>Color:</b> {context.user_data.get('color')}\n"
        f"<b>Sexo:</b> {context.user_data.get('sexo')}"
    )

    if foto_id:
        await update.message.reply_photo(photo=foto_id, caption=resumen, parse_mode="HTML")
    else:
        await update.message.reply_text(resumen, parse_mode="HTML")

    context.user_data.clear()
    return ConversationHandler.END


# =============================================================
# 2. CONSULTA, EDICIÓN Y ELIMINACIÓN DE REPORTES
# =============================================================

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
            .select("id_reporte, id_mascota, tipo_de_reporte, calle, referencia, colonia, codigo_postal, fecha_de_reporte, mascotas(raza, tamano, color, caracteristicas, tiene_collar, sexo, foto_url)")
            .eq("id_usuario", id_usuario)
            .execute()
        )

        if not reportes_res.data:
            await update.message.reply_text("No tienes reportes activos.")
            return ConversationHandler.END

        await update.message.reply_text("<b>Tus Reportes Registrados:</b>", parse_mode="HTML")

        for r in reportes_res.data:
            mascota = r.get("mascotas", {}) or {}
            collar_txt = "Sí" if mascota.get("tiene_collar") else "No"

            texto = (
                f"<b>Reporte #{r['id_reporte']}</b>\n"
                f"<b>Tipo:</b> {r.get('tipo_de_reporte')}\n"
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
    id_reporte = int(partes[1])
    id_mascota = int(partes[2]) if partes[2].isdigit() else None

    try:
        supabase.table("reportes").delete().eq("id_reporte", id_reporte).execute()
        if id_mascota:
            supabase.table("mascotas").delete().eq("id_mascota", id_mascota).execute()

        await query.edit_message_text(f"❌ El <b>Reporte #{id_reporte}</b> fue eliminado correctamente.", parse_mode="HTML")

    except Exception as e:
        print(f"Error al eliminar reporte: {e}")
        await query.edit_message_text("Ocurrió un error al intentar eliminar el reporte.")

    context.user_data.clear()
    return ConversationHandler.END


async def seleccionar_campo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    partes = query.data.split(":")
    context.user_data["edit_id_reporte"] = partes[1]
    context.user_data["edit_id_mascota"] = partes[2]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Calle", callback_data="campo_calle"), InlineKeyboardButton("Colonia", callback_data="campo_colonia")],
        [InlineKeyboardButton("Referencia", callback_data="campo_referencia"), InlineKeyboardButton("Código Postal", callback_data="campo_codigo_postal")],
        [InlineKeyboardButton("Tipo Reporte", callback_data="campo_tipo_de_reporte"), InlineKeyboardButton("Raza", callback_data="campo_raza")],
        [InlineKeyboardButton("Tamaño", callback_data="campo_tamano"), InlineKeyboardButton("Color", callback_data="campo_color")],
        [InlineKeyboardButton("Características", callback_data="campo_caracteristicas"), InlineKeyboardButton("Tiene Collar", callback_data="campo_tiene_collar")],
        [InlineKeyboardButton("Sexo", callback_data="campo_sexo"), InlineKeyboardButton("Nueva Foto", callback_data="campo_foto")]
    ])

    await query.edit_message_text(
        f"Selecciona el campo a modificar del <b>Reporte #{partes[1]}</b>:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    return ELEGIR_CAMPO


async def pedir_nuevo_valor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    campo = query.data.replace("campo_", "")
    context.user_data["edit_campo"] = campo

    instrucciones = {
        "calle": "Escribe la nueva <b>calle</b>:",
        "colonia": "Escribe la nueva <b>colonia</b>:",
        "referencia": "Escribe la nueva <b>referencia</b>:",
        "codigo_postal": "Escribe el nuevo <b>código postal</b>:",
        "tipo_de_reporte": "Escribe el nuevo <b>tipo de reporte</b>:",
        "raza": "Escribe la nueva <b>raza</b>:",
        "tamano": "Escribe el nuevo <b>tamaño</b>:",
        "color": "Escribe el nuevo <b>color</b>:",
        "caracteristicas": "Escribe las nuevas <b>características</b>:",
        "tiene_collar": "Escribe <b>sí</b> o <b>no</b> si cuenta con collar:",
        "sexo": "Escribe el <b>sexo</b> (Macho / Hembra):",
        "foto": "Envía la <b>nueva foto</b> de la mascota:"
    }

    await query.edit_message_text(instrucciones.get(campo, f"Escribe el nuevo valor para {campo}:"), parse_mode="HTML")
    return PEDIR_VALOR


async def guardar_modificacion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    campo = context.user_data.get("edit_campo")
    id_reporte = int(context.user_data.get("edit_id_reporte"))
    id_mascota = int(context.user_data.get("edit_id_mascota"))
    telegram_id = str(update.message.from_user.id)

    nuevo_valor = None

    if campo == "foto":
        if not update.message.photo:
            await update.message.reply_text("No enviaste una imagen. Modificación cancelada.")
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
            campo_db = "foto_url"
        except Exception as err:
            print(f"Error al subir imagen: {err}")
            await update.message.reply_text("Error al subir la imagen.")
            context.user_data.clear()
            return ConversationHandler.END

    elif campo == "tiene_collar":
        texto = update.message.text.strip().lower()
        nuevo_valor = texto in ["si", "sí", "yes", "true"]
        campo_db = "tiene_collar"
    else:
        nuevo_valor = update.message.text
        campo_db = campo

    try:
        if campo_db in ["calle", "colonia", "referencia", "codigo_postal", "tipo_de_reporte"]:
            supabase.table("reportes").update({campo_db: nuevo_valor}).eq("id_reporte", id_reporte).execute()
        elif campo_db in ["raza", "tamano", "color", "caracteristicas", "tiene_collar", "sexo", "foto_url"]:
            supabase.table("mascotas").update({campo_db: nuevo_valor}).eq("id_mascota", id_mascota).execute()

        await update.message.reply_text(f"✅ El campo <b>{campo}</b> fue actualizado correctamente.", parse_mode="HTML")

    except Exception as e:
        print(f"Error al actualizar BD: {e}")
        await update.message.reply_text("Ocurrió un error al actualizar la base de datos.")

    context.user_data.clear()
    return ConversationHandler.END


# =============================================================
# 3. CANCELAR Y MAIN
# =============================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operación cancelada.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # ConversationHandler para Crear Reporte
    conv_crear = ConversationHandler(
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
            TIPO_REPORTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_tipo_reporte)],
            CODIGO_POSTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_codigo_postal)],
            RAZA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_raza)],
            TAMANO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_tamano)],
            CARACTERISTICAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_caracteristicas)],
            COLLAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_collar)],
            COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_color)],
            SEXO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_sexo)],
            FOTO: [MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), recibir_foto)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )

    # ConversationHandler para Editar y Eliminar Reportes
    conv_editar = ConversationHandler(
        entry_points=[CommandHandler("mis_reportes", mis_reportes)],
        states={
            ELEGIR_REPORTE: [
                CallbackQueryHandler(seleccionar_campo, pattern="^edit:"),
                CallbackQueryHandler(eliminar_reporte, pattern="^del:"),
            ],
            ELEGIR_CAMPO: [CallbackQueryHandler(pedir_nuevo_valor, pattern="^campo_")],
            PEDIR_VALOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_modificacion),
                MessageHandler(filters.PHOTO, guardar_modificacion),
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
        per_message=False,
    )

    app.add_handler(conv_crear)
    app.add_handler(conv_editar)

    print("🤖 Bot iniciado y conectado a Supabase con éxito...")
    app.run_polling()


if __name__ == "__main__":
    main()