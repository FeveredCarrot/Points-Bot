import os
import random
import datetime
from abc import ABCMeta, abstractmethod
from urllib.request import Request, urlopen
from pathlib import Path
import glob
import discord
import operator
import pickle
import logging

logging.basicConfig(level=logging.INFO)


prefix = '!'
item_list = {'point': 1, 'high-res blue dragon': 5, 'meme': 10, 'eli': 25, 'small smiling stone face': 50}
eli_list = ['eli.png', 'eli_2.png', 'eli_3.png', 'eli_soren.png', 'real_eli.png', 'year_of_the_rooster.png', 'eli_2.jpg']
rock_list = ['small_smiling_face.jpg']

#vault_path = '/home/pi/Desktop/Vault'
vault_path = 'J:\Vault'
vault_root = vault_path
bank_file = vault_root + '/Points/bank.txt'

accounts = []

client = discord.Client()

def get_account(user):
    for i in accounts:
        if i.name == user:
            return i

def account_not_in_list(user):
    for i in accounts:
        if i.name == user:
            return False
    return True

def create_account(user):
    print('Setting up account for ' + user)
    accounts.append(Account(user))
    for i in item_list:
        get_account(user).give_item(i, 0)
    get_account(user).give_item('point', 5)

async def show_leaderboard(message):
    text = ':checkered_flag: __**Leaderboard**__ :checkered_flag: \n'
    values = {}
    for user in accounts:
        value = 0
        for item in user.items:
            print(item_list[item])
            value += user.items[item].amount * item_list[item]
        values[user.name] = value

    sorted_account_values = sorted(values.items(), key=operator.itemgetter(1))
    sorted_account_values.reverse()
    index = 0;
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


def message_spaces(message):
    spaces = []
    index = 0
    for ch in message.content:
        if ch == ' ':
            spaces.append(index)
        index += 1
    return spaces


class Account(object):

    def __init__(self, user):
        self.name = user
        self.items = {}
        self.last_payday = datetime.datetime.utcnow() - datetime.timedelta(days=1)

    def give_item(self, thing, amount):
        class_names = {'point': 'Point', 'high-res blue dragon': 'HighResBlueDragon', 'eli': 'Eli', 'meme': 'Meme', 'small smiling stone face': 'SmallSmilingStoneFace'}
        if thing in self.items:
            self.items[thing].amount += amount
        else:
            self.items[thing] = globals()[class_names[thing]](self)
            self.items[thing].amount = amount

        with open(bank_file, 'wb') as file:
            pickle.dump(accounts, file)

    async def use_item(self, message, item):
        if self.items[item].amount > 0:
            await self.items[item].use(message)
        else:
            await client.send_message(message.channel, 'Error. You dont have any ' + item + 's')

    async def give(self, message):
        if len(message.mentions) > 0:
            if account_not_in_list(str(message.mentions[0])):
                create_account(str(message.mentions[0]))

            recipient = get_account(str(message.mentions[0]))
            print('recipient:' + str(recipient))
            print('vendor:' + str(message.author))
            #space_counter = 0
            amount_space = 0
            item_space = 0


            spaces = message_spaces(message)
            if len(spaces) >= 2:
                amount_space = spaces[1]
                item_space = spaces[2]
            else:
                await client.send_message(message.channel, 'Error. You did it wrong, dumbass. The correct way is \"!give [@user] [amount] [item]\"')
                return

            if (amount_space == 0 or item_space == 0) or (
                    message.content[amount_space + 1] == ' ' or message.content[item_space + 1] == ' '):
                await client.send_message(message.channel, 'Error. You did it wrong, dumbass. The correct way is \"!give [@user] [amount] [item]\"')
                return
            else:
                amount = int(message.content[amount_space + 1:item_space])
                item = message.content[item_space + 1:]
                if message.content[-1] == 's':
                    item = message.content[item_space + 1: -1]

                if item in self.items:
                    if self.items[item].amount >= amount:
                        self.give_item(item, amount)
                        recipient.give_item(item, amount)
                        await show_leaderboard(message)
                    else:
                        await client.send_message(message.channel, 'Sorry, ' + self.name[:-5] + ', you don\'t have enough ' + item + 's to give.')
                else:
                    await client.send_message(message.channel, 'Sorry, ' + self.name[:-5] + ', you don\'t have any ' + item + 's to give.')
        else:
            await client.send_message(message.channel, 'Error. You did it wrong, dumbass. The correct way is \"!give [@user] [amount] [item]\"')

    async def buy_item(self, message):
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

        if self.items['point'].amount >= item_list[item] * amount:
            self.give_item('point', (0 - item_list[item]) * amount)
            self.give_item(item, amount)
            if amount == 1:
                await client.send_message(message.channel, 'Transaction complete. You bought 1 ' + item)
            else:
                await client.send_message(message.channel, 'Transaction complete. You bought ' + str(amount) + ' ' + item + 's')
        elif amount == 1:
            await client.send_message(message.channel, 'Sorry, you don\'t have enough points to buy any ' + item + 's')
        else:
            await client.send_message(message.channel, 'Sorry, you don\'t have enough points to buy ' + str(amount) + ' ' + item + 's')

    async def sell_item(self, message):
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

        if item in self.items:
            if self.items[item].amount >= amount:
                self.give_item('point', item_list[item] * amount)
                self.give_item(item, 0 - amount)

                if amount == 1:
                    await client.send_message(message.channel, 'Transaction complete. You sold a ' + item + ' for ' + str(item_list[item]) + 'points')
                else:
                    await client.send_message(message.channel, 'Transaction complete. You sold ' + str(amount) + ' ' + item + 's for ' + str(item_list[item] * amount) + ' points')
            else:
                await client.send_message(message.channel, 'Sorry, you don\'t have enough ' + item + '\'s to sell')
        else:
            await client.send_message(message.channel, 'Sorry, you don\'t have any ' + item + '\'s to sell')

    async def send_random_image(self, message):
        files = glob.glob(vault_root + '/*.png')
        files += glob.glob(vault_root + '/*.PNG')
        files += glob.glob(vault_root + '/*.jpg')
        files += glob.glob(vault_root + '/*.JPG')
        files += glob.glob(vault_root + '/*.gif')
        file_index = random.randint(0, len(files))

        await client.send_file(message.channel, files[file_index])

        if files[file_index][len(vault_root) + 1:] in eli_list:
            await client.send_message(message.channel, 'Wow! You found a rare Eli!')
            self.give_item('eli', 1)
        elif files[file_index][len(vault_root) + 1:] in rock_list:
            await client.send_message(message.channel, 'Wow! You found a super rare small smiling stone face!')
            self.give_item('small smiling stone face', 1)

    async def give_random_item(self, message, max_number):
        item = random.choice(list(item_list.keys()))
        amount = random.randint(1, max_number)
        self.give_item(item, amount)
        return [item, amount]

class Item(object):

    def __init__(self, user):
        self.user = user
        self.amount = 0
        self.value = item_list[self.name]


class Point(object):

    def __init__(self, user):
        self.name = 'point'
        self.user = user
        self.amount = 0
        self.value = item_list[self.name]

    async def use(self, message):
        if self.amount > 0:
            await client.send_message(message.channel, 'Who would you like to give this point to?')
            reply = await client.wait_for_message(timeout=300, author=message.author)
            if len(reply.mentions) > 0:
                if account_not_in_list(str(reply.mentions[0])):
                    create_account(str(reply.mentions[0]))
                get_account(str(reply.mentions[0])).give_item('point', 1)
                self.user.give_item('point', -1)
                await client.send_message(message.channel, 'Gave 1 point to ' + str(reply.mentions[0])[:-5])
            else:
                await client.send_message(message.channel, 'Error. Please enter an @mention of who you want to receive the point')
                return
        else:
            await client.send_message(message.channel, 'Error. You don\'t have any points')


class HighResBlueDragon(object):

    def __init__(self, user):
        self.name = 'high-res blue dragon'
        self.user = user
        self.amount = 0
        self.value = item_list[self.name]

    async def use(self, message):
        await client.send_file(message.channel, vault_root + '/high_res_blue_dragon.jpg')


class Eli(object):

    def __init__(self, user):
        self.name = 'eli'
        self.user = user
        self.amount = 0
        self.value = item_list[self.name]

    async def use(self, message):
        await client.send_file(message.channel, vault_root + '/' + eli_list[random.randint(0, len(eli_list))])


class Meme(object):

    def __init__(self, user):
        self.name = 'meme'
        self.user = user
        self.amount = 0
        self.value = item_list[self.name]


    async def use(self, message):
        await client.send_message(message.channel, 'Here is your meme, ' + self.user.name[:-5])
        await self.user.send_random_image(message)


class SmallSmilingStoneFace(object):

    def __init__(self, user):
        self.name = 'small smiling stone face'
        self.user = user
        self.amount = 0
        self.value = item_list[self.name]

    async def use(self, message):
        await client.send_file(message.channel, vault_root + '/' + rock_list[random.randint(0, len(rock_list))])

#client.run('MjU4MDA0MjM1OTAyMjU1MTA1.DIda-g.j6b0db-C-vg1MAkAqpxtbDw1hw4')
