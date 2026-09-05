import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import(
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

NOMBRE, DESCRIPCION, CONFIRMACION = range(3)

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
    user_id = update.message.from_user.id

    datos_reporte = {
        "user_id": user_id,
        "titulo": context.user_data['titulo'],
        "descripcion": context.user_data['descripcion']
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
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )

    app.add_handler(conv_handler)
    print("Bot activo con Supabase")
    app.run_polling()

if __name__ == "__main__":
    main()