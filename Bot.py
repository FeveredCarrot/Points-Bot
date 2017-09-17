from __future__ import unicode_literals

import asyncio
import datetime
import logging
import operator
import os
from pathlib import Path
from urllib.request import Request, urlopen

import discord
import youtube_dl

import classes

logging.basicConfig(level=logging.INFO)

client = discord.Client()
classes.client = client

prefix = '!'
item_list = classes.item_list
eli_list = classes.eli_list
rock_list = classes.rock_list

vault_path = '/home/pi/Desktop/Vault'
# vault_path = 'J:/Vault'
vault_root = vault_path

voice = None
shop_open = False


@client.event
async def on_ready():
    # await discord.opus.load_opus()
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('Invite: https://discordapp.com/oauth2/authorize?client_id={}&scope=bot'.format(client.user.id))
    print('------')


@client.event
async def on_message(message):
    user_name = str(message.author)
    user_account = classes.get_account(user_name)

    if message.content.startswith(prefix):
        if not account_in_list(user_name):
            classes.create_account(str(message.author))

    if message.content.startswith(prefix + 'hey'):
        await client.send_message(message.channel, 'HEY GAMERS')
    elif message.content.startswith(prefix + 'bork'):
        await client.send_message(message.channel, 'eeyaborky', tts=True)
    elif message.content.startswith(prefix + 'vault'):
        # if Path(vault_path).exists():
        if False:
            await the_vault(message)
        else:
            await client.send_message(message.channel, 'Sorry, the vault is GONE')
            return
    elif message.content.startswith(prefix + 'gayzone'):
        if len(message.mentions) > 0:
            if message.mentions[0].voice.voice_channel is None:
                await client.send_message(message.channel,
                                          'Error, target user must be in a voice channel to be GAYZONED')
                return
            else:
                for channel in message.author.server.channels:
                    if channel.name == 'Gay Zone':
                        await client.move_member(message.mentions[0], channel)
                        await client.send_message(message.channel,
                                                  'Get GAYZONED, ' + str(message.mentions[0])[:-5] + '!')
                        return

        else:
            await client.send_message(message.channel, 'Error, please enter an @mention of the person to be Gayzoned')

    elif message.content.startswith(prefix + 'payday') and user_account.using_cipher is False:
        # print((datetime.datetime.utcnow() - get_account(user_name).last_payday).total_seconds())
        if (datetime.datetime.utcnow() - classes.get_account(user_name).last_payday).total_seconds() < 10800:
            await client.send_message(message.channel, 'Sorry, you already got your items recently. Please wait ' + str(
                int((10800 - (datetime.datetime.utcnow() - classes.get_account(
                    user_name).last_payday).total_seconds()) / 60)) + ' more minutes and try again')
            return
        else:
            classes.get_account(user_name).last_payday = datetime.datetime.utcnow()
            stuff = await classes.get_account(user_name).give_random_item(3)
            if stuff[1] == 1:
                await client.send_message(message.channel, 'Cool, you found 1 ' + stuff[0])
            else:
                await client.send_message(message.channel, 'Cool, you found ' + str(stuff[1]) + ' ' + stuff[0] + 's')
    elif message.content.startswith(prefix + 'play'):
        if len(message.content) > 6:
            game = message.content[6:]
            await client.send_message(message.channel, content=(game + 'aborky'), tts=True)
    elif message.channel.name != 'points-bot' and message.content.startswith(prefix):
        await client.send_message(message.channel, 'Hey dumb-dumb, send bot commands in the points-bot channel')
        return
    elif message.content.startswith(prefix + 'give') and user_account.using_cipher is False:
        await classes.get_account(user_name).give(message)
    elif message.content.startswith(prefix + 'leaderboard'):
        await show_leaderboard(message)
    elif message.content.startswith(prefix + 'use') and user_account.using_cipher is False:
        spaces = message_spaces(message)

        if len(spaces) > 0:
            item = message.content[spaces[0] + 1:]
            if len(spaces) > 1:
                item = message.content[spaces[0] + 1: spaces[1]]

            if item not in item_list:
                await client.send_message(message.channel, 'Error. Not a valid item')
                return
            await classes.get_account(user_name).use_item(message, item)
        else:
            await client.send_message(message.channel, 'Error. Please enter an item to use')
            return

    elif message.content.startswith(prefix + 'buy') and user_account.using_cipher is False:
        if len(message.content) > 5:
            await classes.get_account(user_name).buy_item(message)
        else:
            await client.send_message(message.channel,
                                      'Error. You did it wrong, retard. The correct way is \"!buy [amount] [item]\"')
            return
    elif message.content.startswith(prefix + 'sell') and user_account.using_cipher is False:
        if len(message.content) > 6:
            await classes.get_account(user_name).sell_item(message)
        else:
            await client.send_message(message.channel,
                                      'Error. You did it wrong, retard. The correct way is \"!buy [amount] [item]\"')
            return
    elif message.content.startswith(prefix + 'account') and user_account.using_cipher is False:
        user = user_name

        if len(message.mentions) > 0:
            if account_in_list(str(message.mentions[0])):
                user = str(message.mentions[0])
            else:
                await client.send_message(message.channel, 'Error. that person doesn\'t have an account yet')
                return

        text = user[:-5] + '\'s items:\n \n'
        if not account_in_list(user_name):
            classes.create_account(str(message.author))
        for item in classes.get_account(user).items:
            text += str(classes.get_account(user).items[item].amount) + ' ' + item
            if classes.get_account(user_name).items[item].amount == 1:
                text += ' \n'
            else:
                text += 's\n'
        await client.send_message(message.channel, text)
    elif message.content.startswith(prefix + 'shop'):
        await show_shop(message)
    elif message.content.startswith(prefix + 'yt'):
        if message.author.voice.voice_channel is not None:
            if message.content.startswith(prefix + 'yt https://www.youtube.com/watch?v='):
                global voice
                if client.is_voice_connected(message.author.server):
                    print('Disconnecting')
                    for x in client.voice_clients:
                        if x.server == message.server:
                            await x.disconnect()
                            break

                url = message.content[4:]
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': vault_root + '/%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    file_name = ydl.prepare_filename(info)
                    file_name = file_name[:-4] + '.mp3'
                    await client.send_message(message.channel, 'Downloading: ' + file_name[len(vault_root) + 1: -4])
                    # info_dict = ydl.extract_info(url=url, download=False)
                    ydl.download([url])

                voice = await client.join_voice_channel(message.author.voice.voice_channel)
                player = voice.create_ffmpeg_player(file_name)
                await client.send_message(message.channel, 'Playing ' + file_name[len(vault_root) + 1: -4])
                player.start()
                # audio_length = player.duration
                # asyncio.sleep(audio_length)
                # print('Video finished: ' + str(audio_length))
                # for x in client.voice_clients:
                #     if x.server == message.server:
                #         await x.disconnect()
                #         return
            else:
                await client.send_message(message.channel, 'Error. Please enter a valid url')
        else:
            await client.send_message(message.channel, 'Error. You must be in a voice channel to use !yt')
    elif message.content.startswith(prefix + 'heist'):
        heist = classes.Heist()
        await heist.start_heist(message)
    else:
        reply = await client.wait_for_message()
        if len(reply.attachments) > 0 and str(reply.author) != 'Points Bot#7331':
            print(reply.author)
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
            is_done = False
            while not is_done:
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
            document.write(reply.content)
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


def get_length(player):
    while not player.is_stopped():
        asyncio.sleep(5)
        print('Player not stopped')


def account_in_list(user):
    for i in classes.accounts:
        if i.name == user:
            return True
    return False


def message_spaces(message):
    spaces = []
    index = 0
    for ch in message.content:
        if ch == ' ':
            spaces.append(index)
        index += 1
    return spaces


async def show_leaderboard(message):
    text = ':checkered_flag: __**Leaderboard**__ :checkered_flag: \n'
    values = {}
    for user in classes.accounts:
        value = 0
        for item in user.items:
            value += user.items[item].amount * item_list[item].value
        values[user.name] = value

    sorted_account_values = sorted(values.items(), key=operator.itemgetter(1))
    sorted_account_values.reverse()
    index = 0
    for user in sorted_account_values:
        text += ' \n**' + str(user[0][:-5]) + '\'s account:**\n'

        text += str(get_account(str(user[0])).items['point'].amount) + ' ' + 'point'
        if get_account(str(user[0])).items['point'].amount == 1:
            text += ' \n'
        else:
            text += 's\n'
        if sorted_account_values[index][1] == 1:
            text += 'Total value: ' + str(sorted_account_values[index][1]) + ' point\n'
        else:
            text += 'Total value: ' + str(sorted_account_values[index][1]) + ' points\n'
        index += 1

    await client.send_message(message.channel, text)


async def show_shop(message):
    global shop_open
    if shop_open:
        shop_open = False

    text = ':moneybag: Shop :moneybag: \n'
    for item in item_list:
        text += ' \n' + item_list[item].emoji + ' ' + item[0].upper() + item[1:] + ': ' + str(
            item_list[item].value) + ' points'
    text += '\n \nClick on an item react to buy it'
    client_message = await client.send_message(message.channel, text)

    for item in item_list:
        emoji_index = None
        index = 0
        for i in message.server.emojis:
            if str(i) == item_list[item].emoji:
                emoji_index = index
                break
            index += 1
        if emoji_index is None:
            await client.add_reaction(client_message, item_list[item].emoji)
        else:
            await client.add_reaction(client_message, message.server.emojis[emoji_index])

    await asyncio.sleep(0.5)
    items = {}
    for item in item_list:
        items[item_list[item].emoji] = item_list[item]
    shop_open = True

    while True:
        reply = await client.wait_for_reaction(emoji=None)

        if not shop_open:
            return
        if reply is None:
            print('bad')
            return
        if str(reply[0].emoji) in items:
            user = str(reply[1])
            emoji = str(reply[0].emoji)
            if classes.account_not_in_list(user):
                classes.create_account(user)

            user_account = classes.get_account(user)
            if user_account.items['point'].amount >= items[emoji].value:
                user_account.give_item(items[emoji].name, 1)
                user_account.give_item('point', 0 - items[emoji].value)
                await client.send_message(message.channel,
                                          'Transaction complete. ' + user_account.name[:-5] + ' bought 1 ' + items[
                                              emoji].name)
            else:
                await client.send_message(message.channel, 'Sorry, ' + user_account.name[
                                                                       :-5] + ', you don\'t have enough points to buy any ' +
                                          items[emoji].name + 's')
        else:
            print('Emoji not in emoji list')


client.run('MjU4MDA0MjM1OTAyMjU1MTA1.DIda-g.j6b0db-C-vg1MAkAqpxtbDw1hw4')
