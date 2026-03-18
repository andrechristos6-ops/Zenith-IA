import discord
import os
from openai import OpenAI
from dotenv import load_dotenv
from discord import app_commands
from motor.motor_asyncio import AsyncIOMotorClient

# Carrega as chaves do arquivo .env
load_dotenv()

# Configurações do Bot e API
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URL = os.getenv("MONGO_URL") # Adicione sua URL do MongoDB no arquivo .env

# --- CONFIGURAÇÕES ZENITH APPLICATIONS ---
SERVIDORES_AUTORIZADOS = [1452042674264871076] 
LINK_SUPORTE = "https://discord.gg/HK3vQpHQ5g"
ID_CARGO_CLIENTE = 123456789012345678 # <--- TROQUE PELO ID DO SEU CARGO DE CLIENTE
# -----------------------------------------------

# Conexão com o Banco de Dados (Mesmo do Zenith Keys)
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client['test'] # Nome do banco padrão
keys_collection = db['keys']

CHAR_NAME = "Zenith IA"
CHAR_DETAILS = """
(Sua descrição original mantida para preservar a personalidade)
"""

SYSTEM_PROMPT = f"You are roleplaying as {CHAR_NAME}.\n{CHAR_DETAILS}\nRULES: 1. Stay in character. 2. Keep replies SHORT. 3. Professional style."

class ZenithBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sincroniza os comandos Slash
        await self.tree.sync()

bot = ZenithBot()
client_ai = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
chat_history = []

@bot.event
async def on_ready():
    print(f'--- ZENITH IA ONLINE: {bot.user} ---')
    await bot.change_presence(activity=discord.Game(name="discord.gg/HK3vQpHQ5g"))

# --- COMANDO DE RESGATE DE KEYS ---
@bot.tree.command(name="resgatar", description="Ative sua licença profissional da Zenith")
async def resgatar(interaction: discord.Interaction, chave: str):
    await interaction.response.defer(ephemeral=True)

    # Busca a chave no banco de dados compartilhado
    dados_chave = await keys_collection.find_one({"key": chave})

    if not dados_chave:
        return await interaction.followup.send("❌ **Chave inválida ou inexistente.**", ephemeral=True)

    if dados_chave.get("used"):
        return await interaction.followup.send("⚠️ **Esta licença já foi ativada anteriormente.**", ephemeral=True)

    # Atualiza o banco de dados
    await keys_collection.update_one(
        {"key": chave},
        {"$set": {"used": True, "usedBy": str(interaction.user.id)}}
    )

    # Entrega do cargo
    cargo = interaction.guild.get_role(ID_CARGO_CLIENTE)
    msg_cargo = ""
    if cargo:
        try:
            await interaction.user.add_roles(cargo)
            msg_cargo = "\n✅ Seu cargo de acesso foi aplicado."
        except:
            msg_cargo = "\n⚠️ Erro ao aplicar cargo. Contate o suporte."

    embed = discord.Embed(
        title="🚀 Licença Ativada | Zenith Applications",
        description=f"Olá {interaction.user.mention}, sua chave foi validada com sucesso!{msg_cargo}",
        color=0x00FFFF
    )
    embed.set_footer(text="Infraestrutura Cloud Zenith")
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # Verificação de Licença do Servidor
    if message.guild and message.guild.id not in SERVIDORES_AUTORIZADOS:
        embed = discord.Embed(title="⚠️ Acesso Restrito", description="Servidor sem licença ativa.", color=0xFF0000)
        await message.channel.send(embed=embed)
        await message.guild.leave()
        return

    # Lógica de Chat IA
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        async with message.channel.typing():
            content = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '')
            chat_history.append({"role": "user", "content": content})
            
            response = client_ai.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + chat_history[-10:]
            )
            
            reply = response.choices[0].message.content
            await message.reply(reply)

bot.run(DISCORD_TOKEN)