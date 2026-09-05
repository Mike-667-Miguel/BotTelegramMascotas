import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from supabase import create_client, Client

SUPABASE_URL = "https://mttibdgzimylqbkrgyuc.supabase.co"
SUPABASE_KEY = "sb_publishable_iMZxKu40Gfdshdp206JBbA_-QIdPLkr"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def guardar_en_bd(datos: dict) -> bool:
    try:
        respuesta = supabase.table("reportes").insert(datos).execute()
        print(f"¡Guardado con éxito en Supabase!: {respuesta.data}")
        return True
    except Exception as e:
        print(f"Error al guardar en la BD: {e}")
        return False

# Definición de estados para la conversación
(
    NOMBRE,
    DESCRIPCION,
    REPORTE_NOMBRE,
    REPORTE_TELEFONO,
    REPORTE_FECHA,
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
    FOTO
) = range(17)

async def start_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "**Nuevo Reporte**\nPor favor, escribe el nombre o título del reporte:"
    )
    return NOMBRE

async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['titulo'] = update.message.text
    await update.message.reply_text("Genial. Ahora escribe la descripción detallada del problema/reporte:")
    return DESCRIPCION

async def recibir_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['descripcion'] = update.message.text
    await update.message.reply_text("Nombre de quien realiza el reporte:")
    return REPORTE_NOMBRE

async def recibir_reporte_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['reporte_nombre'] = update.message.text
    await update.message.reply_text("Número de teléfono de quien realiza el reporte:")
    return REPORTE_TELEFONO

async def recibir_reporte_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['reporte_telefono'] = update.message.text
    await update.message.reply_text("Fecha de reporte:")
    return REPORTE_FECHA

async def recibir_reporte_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['reporte_fecha'] = update.message.text
    await update.message.reply_text("Calle (Calle donde se encontró o perdió a la mascota):")
    return CALLE

async def recibir_calle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['calle'] = update.message.text
    await update.message.reply_text("Referencias del lugar:")
    return REFERENCIAS

async def recibir_referencias(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['referencias'] = update.message.text
    await update.message.reply_text("Colonia:")
    return COLONIA

async def recibir_colonia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['colonia'] = update.message.text
    await update.message.reply_text("Tipo de reporte (Extravío de mascota / Encontré una mascota):")
    return TIPO_REPORTE

async def recibir_tipo_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['tipo_reporte'] = update.message.text
    await update.message.reply_text("Código postal (Donde se perdió o encontró la mascota):")
    return CODIGO_POSTAL

async def recibir_codigo_postal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['codigo_postal'] = update.message.text
    await update.message.reply_text("Raza del animalito (o lo más aproximado):")
    return RAZA

async def recibir_raza(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['raza'] = update.message.text
    await update.message.reply_text("Tamaño:")
    return TAMANO

async def recibir_tamano(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['tamano'] = update.message.text
    await update.message.reply_text("Características del animalito:")
    return CARACTERISTICAS

async def recibir_caracteristicas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['caracteristicas'] = update.message.text
    await update.message.reply_text("Cuenta con collar (si/no):")
    return COLLAR

async def recibir_collar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['collar'] = update.message.text
    await update.message.reply_text("Color:")
    return COLOR

async def recibir_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['color'] = update.message.text
    await update.message.reply_text("Sexo:")
    return SEXO

async def recibir_sexo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['sexo'] = update.message.text
    await update.message.reply_text("Foto del animalito (envía una imagen):")
    return FOTO

async def recibir_foto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    
    # Obtenemos el archivo con mayor resolución si mandan foto
    foto_id = None
    if update.message.photo:
        foto_id = update.message.photo[-1].file_id
    
    context.user_data['foto'] = foto_id

    datos_reporte = {
        "user_id": user_id,
        "titulo": context.user_data.get('titulo'),
        "descripcion": context.user_data.get('descripcion'),
        "reporte_nombre": context.user_data.get('reporte_nombre'),
        "reporte_telefono": context.user_data.get('reporte_telefono'),
        "reporte_fecha": context.user_data.get('reporte_fecha'),
        "calle": context.user_data.get('calle'),
        "referencias": context.user_data.get('referencias'),
        "colonia": context.user_data.get('colonia'),
        "tipo_reporte": context.user_data.get('tipo_reporte'),
        "codigo_postal": context.user_data.get('codigo_postal'),
        "raza": context.user_data.get('raza'),
        "tamano": context.user_data.get('tamano'),
        "caracteristicas": context.user_data.get('caracteristicas'),
        "collar": context.user_data.get('collar'),
        "color": context.user_data.get('color'),
        "sexo": context.user_data.get('sexo'),
        "foto_id": context.user_data.get('foto')
    }
    
    exito = guardar_en_bd(datos_reporte)

    if exito:
        await update.message.reply_text("¡Reporte guardado exitosamente en la base de datos!")
    else:
        await update.message.reply_text("Hubo un error al guardar el reporte.")

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Reporte cancelado.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token("8691909785:AAEV7e6UEH0wQmpgXP5ixhX6GmJKpKWXe7g").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("reportar", start_reporte)],
        states={
            NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            DESCRIPCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_descripcion)],
            REPORTE_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_reporte_nombre)],
            REPORTE_TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_reporte_telefono)],
            REPORTE_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_reporte_fecha)],
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
            FOTO: [MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, recibir_foto)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )

    app.add_handler(conv_handler)
    print("Bot activo con Supabase")
    app.run_polling()

if __name__ == "__main__":
    main()