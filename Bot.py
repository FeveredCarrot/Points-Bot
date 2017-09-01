import os
import random
import datetime
from urllib.request import Request, urlopen
from pathlib import Path
import glob
import discord
import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)

client = discord.Client()
prefix = '!'
item_list = {'point': 1, 'high-res blue dragon': 5, 'meme': 10, 'eli': 25, 'point voucher': 0, 'small smiling stone face': 50}
eli_list = ['eli.png', 'eli_2.png', 'eli_3.png', 'eli_soren.png', 'real_eli.png', 'year_of_the_rooster.png']
rock_list = ['small_smiling_face.jpg']

vault_path = '/home/pi/Desktop/Vault'
#vault_path = 'J:\Vault'
vault_root = vault_path

date_file = vault_root + '/Points/dates.json'
file = open(date_file, 'r')

dates = {}

if len(file.read()) > 0:
    file.close()
    with open(date_file, 'r') as f:
        dates = json.load(f)
    f.close()

bank_file = vault_root + '/Points/bank.json'
file = open(bank_file, 'r')

accounts = {}

if len(file.read()) > 0:
    file.close()
    with open(bank_file, 'r') as f:
        accounts = json.load(f)
    f.close()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('Invite: https://discordapp.com/oauth2/authorize?client_id={}&scope=bot'.format(client.user.id))
    print('------')


@client.event
async def on_message(message):
    if message.content.startswith(prefix + 'hey'):
        await client.send_message(message.channel, 'HEY GAMERS')
    elif message.content.startswith(prefix + 'vault'):

        if Path(vault_path).exists():
            await the_vault(message)
        else:
            await client.send_message(message.channel, 'Sorry, the vault is GONE')
            return
    elif message.content.startswith(prefix + 'give'):
        await points(message)
    elif message.content.startswith(prefix + 'leaderboard'):
        await show_leaderboard(message)
    elif message.content.startswith(prefix + 'use'):
        await use_item(message, message.content[5:])
    elif message.content.startswith(prefix + 'daily'):
        if str(message.author) in dates:
            if datetime.date.today().strftime('%m, %d') == dates[str(message.author)]:
                await client.send_message(message.channel, 'Sorry, you already got your daily items. Please try again tomorrow')
                return
            else:
                await give_random_item(str(message.author), message)
                dates[str(message.author)] = datetime.date.today().strftime('%m, %d')
                with open(date_file, 'w') as file:
                    json.dump(dates, file)
                file.close()
        else:
            await give_random_item(str(message.author), message)
            dates[str(message.author)] = datetime.date.today().strftime('%m, %d')
            with open(date_file, 'w') as file:
                json.dump(dates, file)
            file.close()
    elif message.content.startswith(prefix + 'buy'):
        if len(message.content) > 5:
            await buy_item(message)
        else:
            await client.send_message(message.channel, 'Error. You did it wrong, retard. The correct way is \"!buy [amount] [item]\"')
            return
    elif message.content.startswith(prefix + 'sell'):
        if len(message.content) > 6:
            await sell_item(message)
        else:
            await client.send_message(message.channel, 'Error. You did it wrong, retard. The correct way is \"!buy [amount] [item]\"')
            return
    elif message.content.startswith(prefix + 'account'):
        text = str(message.author)[:-5] + '\'s items:\n \n'
        if str(message.author) not in accounts:
            create_account(str(message.author))

        for item in accounts[str(message.author)]:
            text += str(accounts[str(message.author)][item]) + ' ' + item
            if accounts[str(message.author)][item] == 1:
                text += ' \n'
            else:
                text += 's\n'
        await client.send_message(message.channel, text)
    elif message.content.startswith(prefix + 'shop'):
        await show_shop(message)
    elif message.content.startswith(prefix + 'play'):
        if len(message.content) > 6:
            game = message.content[6:]
            await client.send_message(message.channel, content=(game + 'aborky'),tts=True)
    else:
        reply = await client.wait_for_message()
        if len(reply.attachments) > 0 and str(message.author) is not 'Points Bot#7331':
            req = Request(reply.attachments[0]["proxy_url"], headers={'User-Agent': 'Mozilla/5.0'})
            webpage = urlopen(req).read()
            image = open(vault_path + '/' + str(reply.attachments[0]["filename"]), 'wb')
            image.write(webpage)
            image.close()
            print("saved " + str(reply.attachments[0]["filename"]))


@client.event
async def on_channel_pins_update():
    print('cool')


async def the_vault(message):
    await client.send_message(message.channel, ':lock: ' + message.author.name + ' Connected to The Vault :lock:')
    stopped = False
    while not stopped:
        await client.send_message(message.channel,
                                  'What would you like to do? \n\n 1. List files \n 2. Open folder/file \n 3. Create folder\n 4. Create text document\n 5. Upload image\n 6. Quit')
        reply = await client.wait_for_message(timeout=300, author=message.author)

        while reply.content != "1" and reply.content != "2" and reply.content != "3" and reply.content != "4" and reply.content != "5" and reply.content != "6":
            await client.send_message(message.channel, 'Please type an actual response')
            reply = await client.wait_for_message(timeout=300, author=message.author)

        if reply.content == "1":

            if Path(vault_path).is_dir():
                file_list = list_files(vault_path)
                await client.send_message(message.channel,
                                          'Files in ' + vault_path[len(vault_root) + 1:] + ':\n\n' + str(file_list))
            else:
                get_containing_folder(vault_path)
                file_list = list_files(vault_path)
                await client.send_message(message.channel,
                                          'Files in ' + vault_path[len(vault_root) + 1:] + ':\n\n' + str(file_list))

        elif reply.content == "2":
            isDone = False
            while isDone == False:
                await client.send_message(message.channel,
                                          'Enter name of folder/file, or type \"stop\" to go back to menu')
                reply = await client.wait_for_message(timeout=300, author=message.author)

                if reply.content.startswith("stop"):
                    break
                elif Path(vault_path + '/' + reply.content).exists():
                    if Path(vault_path + '/' + reply.content).is_file():
                        if reply.content[-4:].lower() == ".png" or reply.content[-4:].lower() == ".jpg":
                            await client.send_file(message.channel, vault_path + '/' + reply.content)
                        elif reply.content[-4:].lower() == ".txt":
                            file = open(vault_path + '/' + reply.content, 'r')
                            update_vault_path(vault_path + '/' + reply.content)
                            await client.send_message(message.channel,
                                                      'File ' + reply.content + ':\n\n' + str(file.read()))
                            file.close()
                        else:
                            await client.send_message(message.channel,
                                                      'Can\'t open file! Unsupported file type! Tell Jasper to fix it.')
                    else:
                        update_vault_path(vault_path + '/' + reply.content)
                        file_list = list_files(vault_path)
                        await client.send_message(message.channel,
                                                  'Opened folder: ' + reply.content + '\nFolder contents:\n\n' + str(
                                                      file_list) + ' \n .')
                else:
                    await client.send_message(message.channel, 'That\'s not a file stupid')

        elif reply.content == "3":
            await client.send_message(message.channel, 'Enter folder name')
            reply = await client.wait_for_message(timeout=300, author=message.author)
            if Path(vault_path + '/' + reply.content).exists():
                await client.send_message(message.channel, 'That folder already exists, dummy!')
            else:
                os.mkdir(vault_path + '/' + reply.content)
                update_vault_path(vault_path + '/' + reply.content)
                await client.send_message(message.channel, 'Created folder ' + vault_path[3:])

        elif reply.content == "4":
            await client.send_message(message.channel, 'Enter document title')
            reply = await client.wait_for_message(timeout=300, author=message.author)
            document = open(vault_path + '/' + reply.content + '.txt', "w")
            await client.send_message(message.channel, 'Enter document contents')
            reply = await client.wait_for_message(timeout=300, author=message.author)
            document.write(reply.content);
            document.close()

        elif reply.content == "5":
            await client.send_message(message.channel, 'Enter image name')
            reply = await client.wait_for_message(timeout=300, author=message.author)
            image_name = reply.content

            await client.send_message(message.channel, 'Upload the image, \"' + image_name + "\"")
            sent_image = False
            while not sent_image:
                reply = await client.wait_for_message(timeout=300, author=message.author)
                if len(reply.attachments) > 0:
                    print("url: " + str(reply.attachments[0]))
                    req = Request(reply.attachments[0]["proxy_url"], headers={'User-Agent': 'Mozilla/5.0'})
                    webpage = urlopen(req).read()
                    image = open(vault_path + '/' + image_name + str(reply.attachments[0]["proxy_url"])[-4:], 'wb')
                    image.write(webpage)
                    image.close()

                    await client.send_message(message.channel, image_name + " uploaded")
                    sent_image = True
                else:
                    await client.send_message(message.channel, 'I said send an IMAGE please!')

        elif reply.content == "6":
            await client.send_message(message.channel, 'Goodbye')
            stopped = True
            return


def update_vault_path(new_path):
    global vault_path
    vault_path = new_path


def list_files(path):
    files = os.listdir(path)
    files.sort()
    file_text = ''

    for i in files:
        if len(file_text) >= 1850:
            file_text += "\n Etc......"
            return file_text
        else:
            file_text += i + '\n'

    print(file_text)
    if len(files) <= 0:
        file_text = 'No files in folder'

    return file_text


def get_containing_folder(path):
    index = -1
    ch = path[index]
    while ch != "/":
        index -= 1
        ch = path[index]

    print(path[-1:index])
    global vault_path
    vault_path = path[:index]


async def points(message):
    if len(message.mentions) > 0:
        user = message.mentions[0]
        print('user:' + str(user))
        print('author:' + str(message.author))
        space_counter = 0
        amount_space = 0
        item_space = 0
        index = 0
        for ch in message.content:
            if ch == ' ':
                space_counter += 1
                if space_counter == 2:
                    amount_space = index
                elif space_counter == 3:
                    item_space = index
            index += 1

        if (amount_space == 0 or item_space == 0) or (
                message.content[amount_space + 1] == ' ' or message.content[item_space + 1] == ' '):
            await client.send_message(message.channel, 'Error. You did it wrong, retard. The correct way is \"!give [@user] [amount] [item]\"')
            return
        else:
            amount = int(message.content[amount_space:item_space])
            item = message.content[item_space + 1:]
            if message.content[-1] == 's':
                item = message.content[item_space + 1: -1]

            if str(message.author) in accounts:
                if item in accounts[str(message.author)]:
                    if accounts[str(message.author)][item] >= amount:
                        accounts[str(message.author)][item] -= amount
                        give_item(str(user), item, amount)
                        await show_leaderboard(message)
                    else:
                        await client.send_message(message.channel, 'Sorry, ' + str(message.author)[:-5] + ', you don\'t have enough ' + item + 's to give.')
                else:
                    await client.send_message(message.channel, 'Sorry, ' + str(message.author)[:-5] + ', you don\'t have any ' + item + 's to give.')
            else:
                create_account(str(message.author))
                accounts[str(message.author)][item] -= amount
                give_item(str(user), item, amount)
    else:
        await client.send_message(message.channel, 'Error. You did it wrong, retard. The correct way is \"!give [@user] [amount] [item]\"')


async def use_item(message, item):
    if item in item_list:
        if accounts[str(message.author)][item] > 0:
            if item.lower() == 'point':
                await client.send_message(message.channel, 'Who would you like to give point to?')
                reply = await client.wait_for_message(timeout=300, author=message.author)
                if len(reply.mentions) > 0:
                    give_item(str(reply.mentions[0]), 'point', 1)
                else:
                    await client.send_message(message.channel, 'Error. Please enter an @mention of who you want to receive the point')
                    return
            elif item.lower() == 'high-res blue dragon':
                await client.send_file(message.channel, vault_root + '/high_res_blue_dragon.jpg')
            elif item.lower() == 'eli':
                await client.send_file(message.channel, vault_root + '/' + eli_list[random.randint(0, len(eli_list))])
            elif item.lower() == 'meme':
                await client.send_message(message.channel, 'Here is your meme, ' + str(message.author)[:-5])
                await send_random_image(message)
            elif item.lower() == 'point voucher':
                await client.send_message(message.channel, 'Who would you like to give this point to?')
                reply = await client.wait_for_message(timeout=300, author=message.author)
                if len(reply.mentions) > 0:
                    give_item(str(reply.mentions[0]), 'point', 1)
                    give_item(str(message.author), 'point voucher', -1)
                    await client.send_message(message.channel, 'Gave 1 point to ' + str(reply.mentions[0]))
                else:
                    await client.send_message(message.channel, 'Error. Please enter an @mention of who you want to receive the point')
                    return
            elif item.lower() == 'small smiling stone face':
                await client.send_file(message.channel, vault_root + '/small_smiling_face.jpg')

            give_item(str(message.author), item, -1)
        else:
            await client.send_message(message.channel, 'Error. You don\'t have any ' + item + "s")
    else:
        await client.send_message(message.channel, 'Error. ' + item[0].upper() + item[1:].lower() + ' isn\'t a real item. Tell Jasper to add it.')


async def buy_item(message):
    space_counter = 0
    amount_space = 0
    item_space = 0
    index = 0
    for ch in message.content:
        if ch == ' ':
            space_counter += 1
            if space_counter == 1:
                amount_space = index
            elif space_counter == 2:
                item_space = index
        index += 1

    if (amount_space == 0 or item_space == 0) or (message.content[amount_space + 1] == ' ' or message.content[item_space + 1] == ' '):
        await client.send_message(message.channel, 'Error. You did it wrong, retard. The correct way is \"!buy [amount] [item]\"')
        return
    else:
        amount = int(message.content[amount_space:item_space])

        if amount < 0:
            await client.send_message(message.channel, 'Error. You can\'t buy a negative number of items')
            return

        item = message.content[item_space + 1:]
        if message.content[-1] == 's':
            item = message.content[item_space + 1: -1]
    if str(message.author) not in accounts:
        create_account(str(message.author))
    if accounts[str(message.author)]['point'] >= item_list[item] * amount:
        give_item(str(message.author), 'point', (0 - item_list[item]) * amount)
        give_item(str(message.author), item, amount)
        if amount == 1:
            await client.send_message(message.channel, 'Transaction complete. You bought a ' + item)
        else:
            await client.send_message(message.channel, 'Transaction complete. You bought ' + str(amount) + ' ' + item + 's')
    elif amount ==1:
        await client.send_message(message.channel, 'Sorry, you don\'t have enough points to buy ' + str(amount) + ' ' + item)
    else:
        await client.send_message(message.channel, 'Sorry, you don\'t have enough points to buy ' + str(amount) + ' ' + item + 's')


async def sell_item(message):
    space_counter = 0
    amount_space = 0
    item_space = 0
    index = 0
    for ch in message.content:
        if ch == ' ':
            space_counter += 1
            if space_counter == 1:
                amount_space = index
            elif space_counter == 2:
                item_space = index
        index += 1

    if (amount_space == 0 or item_space == 0) or (message.content[amount_space + 1] == ' ' or message.content[item_space + 1] == ' '):
        await client.send_message(message.channel, 'Error. You did it wrong, retard. The correct way is \"!sell [amount] [item]\"')
        return
    else:
        amount = int(message.content[amount_space:item_space])

        if amount < 0:
            await client.send_message(message.channel, 'Error. You can\'t sell a negative number of items')
            return

        item = message.content[item_space + 1:]
        if message.content[-1] == 's':
            item = message.content[item_space + 1: -1]
    if str(message.author) not in accounts:
        create_account(str(message.author))

    if item in accounts[str(message.author)]:
        if accounts[str(message.author)][item] >= amount:
            give_item(str(message.author), 'point', item_list[item] * amount)
            give_item(str(message.author), item, 0 - amount)

            if amount == 1:
                await client.send_message(message.channel, 'Transaction complete. You sold a ' + item + ' for ' + str(item_list[item]) + 'points')
            else:
                await client.send_message(message.channel, 'Transaction complete. You sold ' + str(amount) + ' ' + item + 's for ' + str(item_list[item] * amount) + ' points')
        else:
            await client.send_message(message.channel, 'Sorry, you don\'t have enough ' + item + '\'s to sell')
    else:
        await client.send_message(message.channel, 'Sorry, you don\'t have any ' + item + '\'s to sell')


def give_item(user_name, thing, amount):
    if user_name in accounts:
        if thing in accounts[user_name]:
            accounts[user_name][thing] += amount
        else:
            accounts[user_name][thing] = amount

    else:
        create_account(user_name)
        if thing in accounts[user_name]:
            accounts[user_name][thing] += amount
        else:
            accounts[user_name][thing] = amount

    with open(bank_file, 'w') as file:
        json.dump(accounts, file)
    file.close()


async def give_random_item(user, message):
    #list_index = random.randint(0, len(item_list))
    item = random.choice(list(item_list.keys()))
    amount = random.randint(1, 5)
    give_item(user, item, amount)

    if amount == 1:
        await client.send_message(message.channel, 'Here, you got ' + str(amount) + ' ' + item)
    else:
        await client.send_message(message.channel, 'Here, you got ' + str(amount) + ' ' + item + 's')


def create_account(user):
    print('Setting up account for ' + user)
    accounts[user] = {'point': 5}
    for i in item_list:
        give_item(user, i, 0)


async def show_leaderboard(message):
    text = '-Leaderboard-\n'
    for user in accounts:
        text += ' \n' + user[:-5] + '\'s items:\n'
        for item in accounts[user]:
            text += str(accounts[user][item]) + ' ' + str(item)
            if accounts[user][item] == 1:
                text += ' \n'
            else:
                text += 's\n'
    await client.send_message(message.channel, text)


async def show_shop(message):
    text = ':moneybag: Shop :moneybag: \n'
    for item in item_list:
        text += ' \n' + item[0].upper() + item[1:] + ': ' + str(item_list[item]) + ' points'
    await client.send_message(message.channel, text)

async def send_random_image(message):
    files = glob.glob(vault_root + '/*.png')
    files += glob.glob(vault_root + '/*.jpg')
    file_index = random.randint(0, len(files))
    await client.send_file(message.channel, files[file_index])
    if files[file_index][len(vault_root) + 1:] in eli_list:
        await client.send_message(message.channel, 'Wow! You found a rare Eli!')
        give_item(str(message.author), 'eli', 1)
    elif files[file_index][len(vault_root) + 1:] in rock_list:
        await client.send_message(message.channel, 'Wow! You found a rare small smiling stone face!')
        give_item(str(message.author), 'small smiling stone face', 1)


client.run('MjU4MDA0MjM1OTAyMjU1MTA1.DIda-g.j6b0db-C-vg1MAkAqpxtbDw1hw4')
