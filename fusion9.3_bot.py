import telebot
import re
import requests
from bs4 import BeautifulSoup
import traceback
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

disable_warnings(InsecureRequestWarning)

# Lista de IDs de chat autorizados
authorized_chat_ids = ["1926331176", "2012337742", "-1002203336767"]

bot = telebot.TeleBot('7225738728:AAGzcVVULjbtF0uln_Fkwo5_Bn-MDkM1bwE')

NOMBRE_ARCHIVO = 'Sku.xlsx'

# Diccionario de colores y emojis
COLOR_EMOJI_MAP = {
    'BR': '⚪️ BRANCO',
    'RS': '🌸 ROSA',
    'AZ': '🔵 AZUL',
    'PR': '⚫️ PRETO',
    'VD': '🟢 VERDE',
    'VM': '🔴 VERMELHO',
    'AM': '🟡 AMARELO',
    'RO': '🟣 ROXO',
    'MV': '➕ VERDE',
    'G': '📏 G (Grande)',
    'M': '📏 M (Médio)',
    'P': '📏 P (Pequeno)',
    'GG': '📏 GG (Extra Grande)',
    'XG': '📏 XG (Extra Grande)',
    'XXG': '📏 XXG (Duplo Extra Grande)',
    'XXXG': '📏 XXXG (Triplo Extra Grande)',
    'XL': '📏 XL (Extra Grande)',
    # Agregar más colores según sea necesario
}

def get_color_description(sku_suffix):
    return COLOR_EMOJI_MAP.get(sku_suffix, sku_suffix)

def check_availability(url: str) -> str:
    try:
        print(f"Checking availability for URL: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        items = soup.find_all('a', class_='atributo-item')
        produto_elements = soup.find_all('div', class_='acoes-produto')

        disponibilidade = {
            'disponiveis': set(),
            'indisponiveis': set(),
            'skus_disponiveis': set(),
            'skus_indisponiveis': set()
        }

        for item in items:
            variacao_nome = item.get('data-variacao-nome')
            if 'indisponivel' in item.get('class', []):
                disponibilidade['indisponiveis'].add(variacao_nome)
            else:
                disponibilidade['disponiveis'].add(variacao_nome)

        for produto in produto_elements:
            sku = produto.get('class')[-1].split('-')[-1]
            if 'indisponivel' in produto.get('class', []):
                disponibilidade['skus_indisponiveis'].add(sku)
            elif 'disponivel' in produto.get('class', []):
                disponibilidade['skus_disponiveis'].add(sku)

        disponiveis_str = ', '.join(disponibilidade['disponiveis']) if disponibilidade['disponiveis'] else 'Nenhuma'
        indisponiveis_str = ', '.join(disponibilidade['indisponiveis']) if disponibilidade['indisponiveis'] else 'Nenhuma'
        
        skus_disponiveis_str = '\n'.join(
            f"{sku} = {get_color_description(sku[-2:])}"
            for sku in disponibilidade['skus_disponiveis']
        ) if disponibilidade['skus_disponiveis'] else 'Nenhuma'
        
        skus_indisponiveis_str = '\n'.join(
            f"{sku} = {get_color_description(sku[-2:])}"
            for sku in disponibilidade['skus_indisponiveis']
        ) if disponibilidade['skus_indisponiveis'] else 'Nenhuma'

        result = (
            f"✅ Variedades Disponíveis: \n{skus_disponiveis_str}\n\n"
            f"❌ Variedades Indisponíveis: \n{skus_indisponiveis_str}\n\n"
        )

        print(f"Availability check result: {result}")
        return result
    except Exception as e:
        traceback.print_exc()
        return 'Erro ao verificar a disponibilidade.'

def buscar_sku(sku_procurado):
    columna_sku = 'SKU'

    try:
        df = pd.read_excel(NOMBRE_ARCHIVO)

        columna_ean = 'EAN/GTIN\n (Código Universal)'
        columna_ncm = 'NCM'
        columna_altura = 'Altura (cm)'
        columna_largura = 'Largura (cm)'
        columna_comprimento = 'Comprimento (cm)'
        columna_peso = 'Peso Bruto (Kg)'

        expected_columns = [columna_sku, columna_ean, columna_ncm, columna_altura, columna_largura, columna_comprimento, columna_peso]
        missing_columns = [col for col in expected_columns if col not in df.columns]

        if missing_columns:
            return f"Las siguientes columnas faltan en el archivo Excel: {', '.join(missing_columns)}"

        df[columna_sku] = df[columna_sku].fillna('')

        datos_sku = df[df[columna_sku] == sku_procurado]

        if datos_sku.empty:
            datos_sku = df[df[columna_sku].str.contains(f'^{sku_procurado}', case=False, regex=True)]

        if not datos_sku.empty:
            etiqueta = "(📦PRODUTO RJ FREE)" if sku_procurado.startswith('STO') else "(📊PRODUTO SP VIP)"
            respuesta = f"**Datos para el SKU {sku_procurado}:**\n\n{etiqueta}\n\n"
            # Mostrar apenas a primeira variedade completa
            first_variation = True
            additional_skus = []
            for index, row in datos_sku.iterrows():
                if first_variation:
                    respuesta += f"🔸**SKU**: {row[columna_sku]}\n"
                    respuesta += f"🔸**EAN/GTIN (Código Universal)**: {row[columna_ean]}\n"
                    respuesta += f"🔸**NCM**: {row[columna_ncm]}\n"
                    respuesta += f"🔸**Altura (cm)**: {row[columna_altura]}\n"
                    respuesta += f"🔸**Largura (cm)**: {row[columna_largura]}\n"
                    respuesta += f"🔸**Comprimento (cm)**: {row[columna_comprimento]}\n"
                    respuesta += f"🔸**Peso Bruto (Kg)**: {row[columna_peso]}\n"
                    respuesta += f"🔸**7**: {row['Unnamed: 7'] if 'Unnamed: 7' in row else 'N/A'}\n"
                    respuesta += f"🔸**8**: {row['Unnamed: 8'] if 'Unnamed: 8' in row else 'N/A'}\n"
                    respuesta += "\n"
                    first_variation = False
                else:
                    additional_skus.append(f"➕ {row[columna_sku]}")

            if additional_skus:
                respuesta += "\n".join(additional_skus)
        else:
            respuesta = f"SKU {sku_procurado} no encontrado."

        return respuesta

    except Exception as e:
        traceback.print_exc()
        return 'Erro ao ler o arquivo Excel.'

def format_description(description_html):
    replacements = {
        'Chaleira Elétrica Dobrável': '⚡ Chaleira Elétrica Dobrável',
        'solução perfeita': '💡 solução perfeita',
        'design compacto e inteligente': '📏 design compacto e inteligente',
        'silicone de alta qualidade': '🌿 silicone de alta qualidade',
        'Leve e portátil': '🚀 Leve e portátil',
        'Especificações Técnicas:': '\n\n📊 Especificações Técnicas:',
        'Modelo:': '\n\n🔖 Modelo:',
        'Material:': '\n🔧 Material:',
        'Capacidade:': '\n⚖️ Capacidade:',
        'Voltagem:': '\n🔌 Voltagem:',
        'Potência:': '\n🔋 Potência:',
        'Tipo de Tomada:': '\n🔌 Tipo de Tomada:',
        'Dimensões Aprox.:': '\n\n📐 Dimensões Aproximadas:\n',
        'Peso Aprox:': '\n⚖️ Peso Aproximado:',
        'Itens Inclusos na Embalagem:': '\n\n📦 Itens Inclusos na Embalagem:\n'
    }

    for key, value in replacements.items():
        description_html = description_html.replace(key, value)

    return description_html

# Variable global para almacenar los enlaces de imágenes temporalmente
image_links = []

def handle(message):
    global image_links
    chat_id = str(message.chat.id)
    command = message.text

    if chat_id not in authorized_chat_ids:
        unauthorized_message = f'⚠️ Você não está autorizado a usar este bot.\nSeu ID de Chat: {chat_id}'
        bot.send_message(chat_id, unauthorized_message)
        return

    if re.match(r'http[s]?://www\.gruposhopmix\.com/.*', command):
        try:
            session = requests.Session()
            retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            response = session.get(command, verify=False)

            soup = BeautifulSoup(response.content, 'html.parser')
            product_name = soup.find('h1', class_='nome-produto')
            variations = soup.find_all('a', class_='atributo-item')
            price = soup.find('strong', class_='preco-promocional cor-principal titulo')
            stock = soup.find('b', class_='qtde_estoque')
            description = soup.find('meta', attrs={'name': 'twitter:description'})
            sku = soup.find('span', itemprop='sku')

            if product_name:
                bot.send_message(chat_id, f'🛒 Nome do Produto:\n\n {product_name.text.strip()}')
            if description:
                description_html = description.get('content')
                formatted_description = format_description(description_html)
                formatted_description = (
                    f"📃 **Descrição**\n\n"
                    f"{formatted_description}\n\n"
                )
                bot.send_message(chat_id, formatted_description, parse_mode='Markdown')
            else:
                bot.send_message(chat_id, '❌ Descrição não encontrada.')
            if price:
                bot.send_message(chat_id, f'💲 Preço: {price.text.strip()}')
            if stock:
                bot.send_message(chat_id, f'📦 Estoque: {stock.text.strip()}')

                # Chama a função check_availability para verificar disponibilidade
                disponibilidade_result = check_availability(command)
                bot.send_message(chat_id, disponibilidade_result)
                
                # Adiciona o botão com o link para o canal de disponibilidade
                markup = InlineKeyboardMarkup()
                button = InlineKeyboardButton("Consultar Disponibilidade", url="https://t.me/+W_lx8hX6TIE5NDAx")
                markup.add(button)
                bot.send_message(chat_id, "Clique no botão abaixo para consultar a disponibilidade do produto:", reply_markup=markup)
                
            if sku:
                sku_text = sku.text.strip()
                bot.send_message(chat_id, f'🔖 SKU: {sku_text}')
                respuesta_excel = buscar_sku(sku_text)
                bot.send_message(chat_id, respuesta_excel)

            # Almacena las imágenes en la variable global
            image_links = []
            images = soup.find_all('a', {'data-imagem-grande': True})
            for image in images:
                image_link = image['data-imagem-grande']
                image_links.append(image_link)

            # Crea y envía el botón para ver imágenes
            if image_links:
                markup = InlineKeyboardMarkup()
                button = InlineKeyboardButton("Ver Imágenes", callback_data="ver_imagenes")
                markup.add(button)
                bot.send_message(chat_id, "Clique no botão abaixo para ver as imagens do produto:", reply_markup=markup)

        except Exception as e:
            traceback.print_exc()
            bot.send_message(chat_id, '❌ Erro ao processar a página web. Assegure-se de que seja da shopmix.com.')

    elif re.match(r"^SKU:\s*(\S+)$", command, re.IGNORECASE):
        match = re.match(r"^SKU:\s*(\S+)$", command, re.IGNORECASE)
        if match:
            sku_procurado = match.group(1).upper()
            respuesta = buscar_sku(sku_procurado)
            bot.send_message(chat_id, respuesta)
    else:
        bot.send_message(chat_id, '❌ Página inválida. Certifique-se de enviar um link válido do Shopmix.')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Por favor, envía el link del producto de Shopmix del que deseas obtener información.")

@bot.message_handler(content_types=['new_chat_members'])
def greet_new_member(message):
    for member in message.new_chat_members:
        welcome_message = (
            f'👋 ¡Bemvindo, {member.first_name}!\n\n'
            'E aí, me manda o link do produto da Shopmix que você quer saber mais. '
            'Se tá perdido de como usar o bot, dá uma olhada nesse vídeo tutorial: https://youtu.be/RcQbdjhdhMI?si=C2oK6El9fdIAguBx '
            'Lembre-se de não mandar nenhum dado pessoal e que esse serviço é de graça, viu?.'
        )
        bot.send_message(message.chat.id, welcome_message)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if re.match(r'http[s]?://www\.gruposhopmix\.com/.*', message.text):
        handle(message)
    elif re.match(r"^SKU:\s*(\S+)$", message.text, re.IGNORECASE):
        match = re.match(r"^SKU:\s*(\S+)$", message.text, re.IGNORECASE)
        if match:
            sku_procurado = match.group(1).upper()
            respuesta = buscar_sku(sku_procurado)
            bot.send_message(message.chat.id, respuesta)
    else:
        # Não responder a mensagens que não sejam URLs válidas do Shopmix ou buscas de SKU
        pass

@bot.callback_query_handler(func=lambda call: call.data == "ver_imagenes")
def callback_ver_imagenes(call):
    global image_links
    if image_links:
        for image_link in image_links:
            bot.send_message(call.message.chat.id, f'🖼️ Imagem Original: {image_link}')
        # Vacía la lista de enlaces de imágenes después de enviarlos
        image_links = []
    else:
        bot.send_message(call.message.chat.id, '❌ Nas imagens ja foram consultadas ou não foram encontradas imagens para este produto.')

if __name__ == '__main__':
    print("Bot iniciado...")
    bot.polling()
