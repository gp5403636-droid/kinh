import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
import asyncio

load_dotenv()
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GROUP = os.getenv("GROUP")

# Links iniciais de afiliado
affiliate_links = {
    "shopee": "https://s.shopee.com.br/5L33yfaf2Q",
    "aliexpress": "https://s.click.aliexpress.com/e/_mNHDHYl"
}

# Armazena produtos já postados
posted_products = set()

# Função para formatar mensagens
def format_promo(data):
    return f"""{data['gatilho']}

🛍️ {data['nome']}

De {data['pa']}
💥 Por {data['preco']}
💳 {data['par']}

🏷️ Use o cupom: {data['cp']}

🛒 Compre aqui 👉 {data['link']}

⚠️ Promoção sujeita à alteração de preço e estoque do site"""

# Função para extrair promoções Shopee
def get_shopee_promos():
    url = "https://shopee.com.br/ofertas"
    result = []
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        products = soup.find_all("a", limit=5)
        for p in products:
            title = p.get("title") or "Produto Shopee"
            link = affiliate_links.get("shopee", "https://shopee.com.br")
            result.append({
                "nome": title,
                "link": link,
                "pa": "R$0",
                "preco": "R$0",
                "par": "A vista",
                "cp": "N/A",
                "gatilho": "🔥 OFERTA IMPERDÍVEL 🔥"
            })
    except:
        pass
    return result

# Função para extrair promoções AliExpress
def get_aliexpress_promos():
    url = "https://pt.aliexpress.com/promo.htm"
    result = []
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        products = soup.find_all("a", limit=5)
        for p in products:
            title = p.get("title") or "Produto AliExpress"
            link = affiliate_links.get("aliexpress", "https://aliexpress.com")
            result.append({
                "nome": title,
                "link": link,
                "pa": "US$0",
                "preco": "US$0",
                "par": "À vista",
                "cp": "N/A",
                "gatilho": "💥 OFERTA IMPERDÍVEL 💥"
            })
    except:
        pass
    return result

# Função genérica para outras lojas (exemplo Amazon/Kabum/Magalu/ML)
def get_other_promos():
    # Exemplo simplificado, pode ser expandido
    return []

# Postar promoções no grupo
async def post_promos(context: CallbackContext.DEFAULT_TYPE):
    promos = get_shopee_promos() + get_aliexpress_promos() + get_other_promos()
    for p in promos:
        if p["nome"] not in posted_products:
            posted_products.add(p["nome"])
            msg = format_promo(p)
            await context.bot.send_message(chat_id=GROUP, text=msg, parse_mode="Markdown")

# Comandos Telegram
async def start(update: Update, context: CallbackContext.DEFAULT_TYPE):
    await update.message.reply_text("Bot de promoções ativo!")

async def help_cmd(update: Update, context: CallbackContext.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - iniciar\n/help - ajuda\n/setlink loja link - atualizar link afiliado"
    )

async def setlink(update: Update, context: CallbackContext.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Somente o dono pode atualizar links.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Use: /setlink loja link")
        return
    loja = context.args[0].lower()
    link = context.args[1]
    affiliate_links[loja] = link
    await update.message.reply_text(f"Link de afiliado da {loja} atualizado!")

# Links manuais
async def handle_link(update: Update, context: CallbackContext.DEFAULT_TYPE):
    text = update.message.text
    if "shopee" in text.lower():
        link = affiliate_links.get("shopee", text)
    elif "aliexpress" in text.lower():
        link = affiliate_links.get("aliexpress", text)
    else:
        link = text
    data = {
        "gatilho":"🔥 OFERTA IMPERDÍVEL 🔥",
        "nome":"Produto",
        "pa":"R$0",
        "preco":"R$0",
        "par":"A vista",
        "cp":"N/A",
        "link": link
    }
    msg = format_promo(data)
    await context.bot.send_message(chat_id=GROUP, text=msg, parse_mode="Markdown")

# Configuração do bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("setlink", setlink))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))

# Scheduler automático (30 minutos)
async def scheduler():
    while True:
        await post_promos(app)
        await asyncio.sleep(1800)  # 30 minutos

# Roda bot + scheduler
async def main():
    asyncio.create_task(scheduler())
    await app.run_polling()

if _name_ == "_main_":
    asyncio.run(main())
