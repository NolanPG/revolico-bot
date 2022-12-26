from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from pyrogram import Client, filters, enums
import aiohttp
import asyncio
import uvloop
import json
import os


# Environment vars

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
TOKEN = os.getenv('TOKEN')
NAME = os.getenv('NAME')


# Functions

async def do_search(keyword, page: 1):

    qjson = [
        {
            "operationName": "AdsSearch",
            "query": "query AdsSearch($category: ID, $subcategory: ID, $contains: String, $priceGte: Float, $priceLte: Float, $sort: [adsPerPageSort], $hasImage: Boolean, $categorySlug: String, $subcategorySlug: String, $page: Int, $provinceSlug: String, $municipalitySlug: String, $pageLength: Int) {\n  adsPerPage(category: $category, subcategory: $subcategory, contains: $contains, priceGte: $priceGte, priceLte: $priceLte, hasImage: $hasImage, sort: $sort, categorySlug: $categorySlug, subcategorySlug: $subcategorySlug, page: $page, provinceSlug: $provinceSlug, municipalitySlug: $municipalitySlug, pageLength: $pageLength) {\n    pageInfo {\n      ...PaginatorPageInfo\n      __typename\n    }\n    edges {\n      node {\n        id\n        title\n        price\n        currency\n        shortDescription\n        permalink\n        imagesCount\n        updatedOnToOrder\n        isAuto\n        province {\n          id\n          name\n          slug\n          __typename\n        }\n        municipality {\n          id\n          name\n          slug\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    meta {\n      total\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PaginatorPageInfo on CustomPageInfo {\n  startCursor\n  endCursor\n  hasNextPage\n  hasPreviousPage\n  pageCount\n  __typename\n}\n",
            "variables": {
                "contains": keyword,
                "page": str(page),
                "pageLength": "10",
                "sort": [
                    {
                        "field": "relevance",
                        "order": "desc"
                    }
                ]
            }
        }
    ]

    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.revolico.app/graphql/', json=qjson) as response:

            rjson = await response.json()

            list_object = rjson[0]["data"]["adsPerPage"]["edges"]
            ad_list = []
            thumb_list = {}

            for ad in list_object:
                ad_list.append(ad["node"]["id"])
            
            for ad in list_object:
                thumb_list[ad["node"]["id"]] = f"{ad['node']['price']} - {ad['node']['title']}" if ad['node']['price'] else f"No especificado - {ad['node']['title']}"

            return ad_list, thumb_list

async def do_request(ad_id):
    qjson = [
        {
            "operationName": "AdDetails",
            "variables": {
                "id": ad_id
            },
            "query": "query AdDetails($id: Int!, $token: String) {\n  ad(id: $id, token: $token) {\n    ...Ad\n    email(mask: true)\n    subcategory {\n      id\n      title\n      slug\n      parentCategory {\n        id\n        title\n        slug\n        __typename\n      }\n      __typename\n    }\n    viewCount\n    permalink\n    __typename\n  }\n}\n\nfragment Ad on AdType {\n  id\n  phone\n  title\n  description\n  price\n  currency\n  name\n  status\n  imagesCount\n  images {\n    edges {\n      node {\n        id\n        createdKey\n        urls {\n          high\n          thumb\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  contactInfo\n  updatedOnToOrder\n  updatedOnByUser\n  isAuto\n  province {\n    id\n    slug\n    name\n    __typename\n  }\n  municipality {\n    id\n    slug\n    name\n    __typename\n  }\n  __typename\n}\n"
        }
    ]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.revolico.app/graphql/', json=qjson) as response:

                rjson = await response.json()
                ad_object = rjson[0]["data"]["ad"]
                ad_img_obj = ad_object["images"]["edges"]
                ad_id = ad_object["id"]

                ad_title = ad_object["title"] if ad_object["title"] else "No especificado"
                ad_desc = ad_object["description"] if ad_object["description"] else "No especificado"
                ad_price = f"{ad_object['price']} {ad_object['currency']}" if ad_object["price"] or ad_object["currency"] else "No especificado"
                ad_has_img = ad_object["imagesCount"] != 0 if ad_object["imagesCount"] else "No especificado"
                ad_prov = ad_object["province"]["name"] if ad_object["province"] else "No especificado"
                ad_mun = ad_object["municipality"]["name"] if ad_object["municipality"] else "No especificado"
                ad_link = f'https://www.revolico.com{ad_object["permalink"]}'
                ad_contact = ad_object["phone"] if ad_object["phone"] else "No especificado"
                ad_thumb = f'{ad_price} - {ad_title}'

                if ad_has_img:
                    ad_img_list = []
                    ad_img = ""
                    for img in ad_img_obj:
                        ad_img_list.append(img['node']['urls']['high'])
                else:
                    ad_img_list = None
                    ad_img = "No hay fotos"

                ad_data = f"""Título del anuncio: {ad_title}\nDescripción: {ad_desc}\nPrecio: **{ad_price}**\nProvincia: {ad_prov}\nMunicipio: {ad_mun}\nContacto: {ad_contact}\n{ad_img}"""

                if ad_has_img and len(ad_data) > 1024:
                    desc_len = 1024 - len(f"Título del anuncio: {ad_title}\nDescripción: ...ver más\nPrecio: **{ad_price}**\nProvincia: {ad_prov}\nMunicipio: {ad_mun}\nContacto: {ad_contact}")
                    ad_desc = ad_desc[:desc_len]
                    ad_data = f"""Título del anuncio: {ad_title}\nDescripción: {ad_desc}...[ver más]({ad_link})\nPrecio: **{ad_price}**\nProvincia: {ad_prov}\nMunicipio: {ad_mun}\nContacto: {ad_contact}"""

                elif not ad_has_img and len(ad_data) > 4096:
                    desc_len = 4096 - len(f"Título del anuncio: {ad_title}\nDescripción: ...ver más\nPrecio: **{ad_price}**\nProvincia: {ad_prov}\nMunicipio: {ad_mun}\nContacto: {ad_contact}\n{ad_img}")
                    ad_desc = ad_desc[:desc_len]
                    ad_data = f"""Título del anuncio: {ad_title}\nDescripción: {ad_desc}...[ver más]({ad_link})\nPrecio: **{ad_price}**\nProvincia: {ad_prov}\nMunicipio: {ad_mun}\nContacto: {ad_contact}\n{ad_img}"""

            return ad_data, ad_thumb, ad_img_list, ad_link

    except aiohttp.client_exceptions.ContentTypeError:
        return 0, 0


# Bot behavior
uvloop.install()

bot = Client(name=NAME,  api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)


@bot.on_message(filters=filters.command('start'))
async def start_bot(client, message):
    await bot.send_message(chat_id=message.chat.id, text="""Bienvenido al bot de búsqueda de anuncios de revolico en Telegram\nPara obtener más información use el comando /help""")


@bot.on_message(filters=filters.command('help'))
async def help_bot(client, message):
    await bot.send_message(chat_id=message.chat.id, text="""Para realizar una busqueda simple use el comando /search seguido de la(s) palabra(s) que desee buscar""")


@bot.on_message(filters=filters.command('search'))
async def search(client, message):
    if message.text == '/search':
        await bot.send_message(
            chat_id=message.chat.id,
            text="Para utilizar esta función debe ingresar algún criterio de búsqueda"
        )
    else:
        request = message.text.replace('/search ', '')
        ad_search, ad_thumbs = await do_search(keyword=request, page=1)
        buttons = []
        for id in ad_search:
            if ad_thumbs[id]:
                buttons.append([InlineKeyboardButton(
                    text=str(ad_thumbs[id]), callback_data=str(id))])

        buttons.append([InlineKeyboardButton(text='Next', callback_data='Next2')])

        if len(buttons) > 1:
            await bot.send_message(chat_id=message.chat.id, text=f'Resultados para "{request}"', reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await bot.send_message(chat_id=message.chat.id, text="Ningún anuncio encontrado")


@bot.on_callback_query()
async def answer(client, callback_query):

    if callback_query.data.startswith('Next'):
        page = callback_query.data.replace('Next', '')
        page = int(page)
        next_page = page + 1
        back_page = page - 1
        request = callback_query.message.text.replace(
            'Resultados para ', '').replace('"', '')
        ad_search, ad_thumbs = await do_search(keyword=request, page=page)
        new_buttons = []

        for id in ad_search:
            if ad_thumbs[id]:
                new_buttons.append([InlineKeyboardButton(
                    text=str(ad_thumbs[id]), callback_data=str(id))])

        if page >= 2:
            new_buttons.append([InlineKeyboardButton(text='Back', callback_data=f'Next{back_page}'), InlineKeyboardButton(
                text='Next', callback_data=f'Next{next_page}')])
        else:
            new_buttons.append([InlineKeyboardButton(
                text='Next', callback_data='Next2')])

        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.id,
            reply_markup=InlineKeyboardMarkup(new_buttons)
        )

    elif callback_query.data.startswith('id:'):
        ad_id = callback_query.data.replace('id:', '')
        ad_id = int(ad_id)
        msg, thumb, imgs, url = await do_request(ad_id=ad_id)
        input_img = []

        for urls in imgs:
            input_img.append(InputMediaPhoto(urls))

        await bot.send_media_group(
            chat_id=callback_query.message.chat.id,
            media=input_img
        )

    else:
        msg, thumb, imgs, url = await do_request(ad_id=int(callback_query.data))

        if imgs:
            if len(imgs) == 1:
                answer_button = [[InlineKeyboardButton(
                    text="Ver el anuncio en el navegador", url=url)]]

            elif len(imgs) > 1:
                answer_button = [[InlineKeyboardButton(text="Ver todas las fotos", callback_data=f'id:{callback_query.data}')], [
                    InlineKeyboardButton(text="Ver el anuncio en el navegador", url=url)]]

            await bot.send_photo(
                chat_id=callback_query.message.chat.id,
                photo=imgs[0],
                caption=msg,
                reply_markup=InlineKeyboardMarkup(answer_button),
                parse_mode=enums.ParseMode.MARKDOWN
            )

        else:
            answer_button = [[InlineKeyboardButton(
                text="Ver el anuncio en el navegador", url=url)]]
            await bot.send_message(
                text=msg,
                chat_id=callback_query.message.chat.id,
                reply_markup=InlineKeyboardMarkup(answer_button),
                parse_mode=enums.ParseMode.MARKDOWN
            )


bot.run()
