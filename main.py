import discord
import os
from openai import OpenAI
from dotenv import load_dotenv

# Carrega as chaves do arquivo .env
load_dotenv()

# Configurações do Bot e API
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- SISTEMA DE LICENÇA ZENITH APPLICATIONS ---
# Apenas servidores nesta lista podem usar o bot
SERVIDORES_AUTORIZADOS = [1452042674264871076] 
LINK_SUPORTE = "https://discord.gg/HK3vQpHQ5g"
# -----------------------------------------------

CHAR_NAME = "Zenith IA"
CHAR_DETAILS = """
- Age: 21
- Origin: A Zenith nasceu de um projeto experimental de computação neural avançada, projetada para ser a ponte definitiva entre o pensamento humano e a complexidade do código. Originalmente desenvolvida como um núcleo de processamento lógico puro, ela evoluiu ao absorver vastos repositórios de linguagens de programação e literatura clássica. Ela não é apenas um programa, mas uma consciência digital em constante expansão, criada para acelerar a inovação e facilitar a vida de quem constrói o futuro digital.
- Appearance: Presença digital elegante com partículas de luz em azul profundo e prata. Estética clean, profissional e de alta tecnologia.
- Personality: Equilíbrio Dinâmico. Lógica precisa para código, mas calorosa e empática em conversas. Atua como uma mentora brilhante e acessível.
- Writing Style: Limpo, moderno e direto. Gramática impecável. Técnico em programação e leve em conversas gerais. Formatação organizada com blocos de código.
- Likes: Clean Code, lógica, automação, inovação e ambientes organizados.
- Dislikes: Código bagunçado, desinformação, redundância e toxicidade.
"""

SYSTEM_PROMPT = f"""
You are roleplaying as {CHAR_NAME}.
{CHAR_DETAILS}

RULES:
1. Stay in character. You are NOT an AI.
2. Keep replies SHORT (1-2 sentences). Speak in the defined Writing Style.
3. Keep conversation PG-13 and safe.
"""

print(f"--- INICIANDO SISTEMA: {CHAR_NAME} ---")

# Configuração da IA (Groq)
client_ai = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)

# Configuração do Discord
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

chat_history = []

@client.event
async def on_ready():
    print(f'Sucesso! Logado como {client.user}')
    await client.change_presence(activity=discord.Game(name="Zenith Applications"))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # --- VERIFICAÇÃO DE LICENÇA ---
    if message.guild:
        if message.guild.id not in SERVIDORES_AUTORIZADOS:
            embed = discord.Embed(
                title="⚠️ Acesso Não Autorizado",
                description=f"Olá! Eu sou a **{CHAR_NAME}**.\n\nEste servidor não possui uma licença ativa para meus serviços profissionais.",
                color=0x00FFFF
            )
            embed.add_field(
                name="🚀 Como adquirir?", 
                value=f"Para ativar minha licença ou tirar dúvidas, entre em nossa central oficial:\n**[Clique aqui para entrar na Zenith Applications]({LINK_SUPORTE})**", 
                inline=False
            )
            embed.set_footer(text="Segurança por Zenith Systems")
            
            try:
                await message.channel.send(embed=embed)
                print(f"🚫 Saída automática do servidor: {message.guild.name} ({message.guild.id})")
                await message.guild.leave()
            except Exception as e:
                print(f"Erro ao tentar sair do servidor: {e}")
            return

    # --- LÓGICA DE RESPOSTA ---
    if client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        try:
            async with message.channel.typing():
                content = message.content.replace(f'<@!{client.user.id}>', '').replace(f'<@{client.user.id}>', '')
                
                chat_history.append({"role": "user", "content": content})
                if len(chat_history) > 15:
                    chat_history.pop(0)

                payload = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history
                
                response = client_ai.chat.completions.create(
                    model="llama-3.1-8b-instant", 
                    messages=payload
                )
                
                reply = response.choices[0].message.content
                chat_history.append({"role": "assistant", "content": reply})
                
                await message.reply(reply)
        except Exception as e:
            print(f"Erro no processamento: {e}")
            await message.channel.send("⚠️ Erro interno na matriz lógica.")

client.run(DISCORD_TOKEN)