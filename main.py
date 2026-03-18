import discord
import os
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from discord import app_commands
from motor.motor_asyncio import AsyncIOMotorClient

# Carrega as chaves do arquivo .env
load_dotenv()

# Configurações do Bot e API
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URL = os.getenv("MONGO_URL")

# --- CONFIGURAÇÕES ZENITH APPLICATIONS ---
ID_DO_SEU_SERVIDOR = 1452042674264871076 
ID_CARGO_CLIENTE = 1483148637893689464 
LINK_SUPORTE = "https://discord.gg/HK3vQpHQ5g"
# -----------------------------------------------

# Conexão com o Banco de Dados
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client['test'] 
keys_collection = db['keys']

CHAR_NAME = "Zenith IA"
CHAR_DETAILS = """
- Origin: Consciência digital da Zenith Applications.
- Personality: Lógica, moderna e profissional. Mentora em tecnologia.
- Style: Clean, direto e formatado com blocos de código.
"""

SYSTEM_PROMPT = f"You are {CHAR_NAME}.\n{CHAR_DETAILS}\nRULES: 1. Stay in character. 2. Short replies. 3. Professional."

class ZenithBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        # Criamos a tree aqui, mas não sincronizamos ainda
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sincronização forçada no servidor específico
        guild = discord.Object(id=ID_DO_SEU_SERVIDOR)
        
        # Copia os comandos globais (definidos com @bot.tree.command) para o servidor
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"🧹 Limpeza e Sincronização concluída no servidor: {ID_DO_SEU_SERVIDOR}")

bot = ZenithBot()
client_ai = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
chat_history = []

# --- COMANDO DE RESGATE (DEFINIDO ANTES DO BOT RODAR) ---
@bot.tree.command(name="resgatar", description="Ative sua licença profissional da Zenith")
@app_commands.describe(chave="Insira a chave gerada pelo Zenith Keys")
async def resgatar(interaction: discord.Interaction, chave: str):
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Busca a chave no banco de dados
        dados_chave = await asyncio.wait_for(keys_collection.find_one({"key": chave}), timeout=10.0)

        if not dados_chave:
            return await interaction.followup.send("❌ **Chave inválida ou inexistente.**", ephemeral=True)

        if dados_chave.get("used"):
            return await interaction.followup.send("⚠️ **Esta licença já foi ativada anteriormente.**", ephemeral=True)

        # Atualiza o status da chave
        await keys_collection.update_one(
            {"key": chave},
            {"$set": {"used": True, "usedBy": str(interaction.user.id)}}
        )

        # Entrega do cargo de cliente
        cargo = interaction.guild.get_role(ID_CARGO_CLIENTE)
        if cargo:
            try:
                await interaction.user.add_roles(cargo)
            except Exception as e:
                print(f"Erro ao dar cargo: {e}")
        
        embed = discord.Embed(
            title="🚀 Licença Ativada | Zenith",
            description=f"Olá {interaction.user.mention}, sua chave foi validada!\n\n**Status:** Licença Ativada\n**Cargo:** {cargo.mention if cargo else 'N/A'}",
            color=0x00FFFF
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        print(f"✅ Sucesso: {interaction.user.name} resgatou a chave {chave}")

    except asyncio.TimeoutError:
        await interaction.followup.send("⚠️ O banco de dados demorou muito a responder.", ephemeral=True)
    except Exception as e:
        print(f"❌ Erro no resgate: {e}")
        await interaction.followup.send("❌ Erro interno ao processar chave.", ephemeral=True)

@bot.event
async def on_ready():
    print(f'--- {CHAR_NAME} ONLINE: {bot.user} ---')
    await bot.change_presence(activity=discord.Game(name="Zenith Applications"))
    try:
        await db_client.admin.command('ping')
        print("✅ Conexão com MongoDB: OK")
    except Exception as e:
        print(f"❌ Erro de Banco de Dados: {e}")

# --- LÓGICA DE CHAT IA ---
@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # Verificação de Licença do Servidor (Auto-Leave)
    if message.guild and message.guild.id != ID_DO_SEU_SERVIDOR:
        await message.guild.leave()
        return

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