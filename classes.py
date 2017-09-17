import os
import datetime
import glob
import logging
import operator
import asyncio
import pickle
import random
import scenarios

import discord

logging.basicConfig(level=logging.INFO)

prefix = '!'

eli_list = ['eli.png', 'eli_2.png', 'eli_3.png', 'eli_soren.png', 'real_eli.png', 'year_of_the_rooster.png',
            'eli_2.jpg']
rock_list = ['small_smiling_face.jpg', 'magik.png',
             'eJwFwdsNwyAMAMBdGABT8wjONhQQSZXUCLtfVXfv3dd81mV2c6hO2QHaKZVXs6K8yuh2MI-rl3mKrXxDUS31uPtbBTYXCR2lEDLm.jpg']

vault_root = '/home/pi/Desktop/Vault'
#vault_root = 'J:/Vault'
vault_path = vault_root
bank_file = vault_root + '/Points/bank.txt'

client = discord.Client()


def get_account(user):
    for account in accounts:
        if account.name == user:
            return account


def account_not_in_list(user):
    for i in accounts:
        if i.name == user:
            return False
    return True


def create_account(user):
    print('Setting up account for ' + user)
    accounts.append(Account(user))
    for item in item_list:
        get_account(user).give_item(item, 0)
    get_account(user).give_item('point', 5)


def delete_account(user):
    if account_not_in_list(user):
        print('That user doesnt exist!')

    user = get_account(user)
    accounts.remove(user)


async def show_leaderboard(message):
    text = ':checkered_flag: __**Leaderboard**__ :checkered_flag: \n'
    values = {}
    for user in accounts:
        value = 0
        for item in user.items:
            print(item_list[item])
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

def account_in_list(user):
    for i in accounts:
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


class Heist(object):
    def __init__(self):
        self.heist_users = {}
        self.heist_items = {'gun': 0, 'rope': 0, 'cipher': 0, 'tool': 0}
        self.react_list = {'🔫': 'gun', '<:rope:357349458607865857>': 'rope', '💻': 'cipher', '🛠': 'tool',
                           '<:facewithstuckouttongueandwinking:304763680707444736>': 'talk', '🏃': 'run'}
        self.heist_started = False
        self.number_of_scenarios = {'intro': 1, 'room': 0, 'vault': 1, 'getaway': 1}

        scenarios.client = client
        scenarios.react_list = self.react_list
        scenarios.item_list = item_list


    async def start_heist(self, message):
        scenarios.channel = message.channel

        time_left = 20
        text = self.start_text(message, time_left)
        message = await client.send_message(message.channel, text)
        await self.add_reacts(message, self.react_list)
        asyncio.ensure_future(self.get_bought_items(message))

        while time_left > 0:
            await asyncio.sleep(1)
            time_left -= 1
            text = self.start_text(message, time_left)
            await client.edit_message(message, text)
        self.heist_started = True
        scenarios.heist_in_progress = True

        self.number_of_scenarios['room'] = random.randint(2, 5)

        while self.number_of_scenarios['intro'] > 0:
            await scenarios.start_random_intro()
            self.number_of_scenarios['intro'] -= 1


    async def get_bought_items(self, message):
        while True:

            if self.heist_started:
                return
            reply = await client.wait_for_reaction(emoji=None)

            if self.heist_started:
                return

            if reply is None:
                print('Timeout or something')
                return

            if str(reply[0].emoji) in self.react_list:
                user = str(reply[1])
                if user != 'Points Bot#7331':
                    print(user)
                    emoji = str(reply[0].emoji)
                    if account_not_in_list(user):
                        create_account(user)

                    user_account = get_account(user)
                    if user_account.items['point'].amount >= item_list[self.react_list[emoji]].value:
                        self.heist_items[item_list[self.react_list[emoji]].name] += 1
                        user_account.give_item('point', -item_list[self.react_list[emoji]].value)
                        if user_account not in scenarios.crew:
                            scenarios.crew.append(user_account)
                        await client.send_message(message.channel, user_account.name[:-5] + ' bought 1 ' + item_list[
                            self.react_list[emoji]].name + ' for the crew')

                    else:
                        await client.send_message(message.channel, 'Sorry, ' + user_account.name[
                                                                               :-5] + ', you don\'t have enough points to buy any ' +
                                                  item_list[self.react_list[emoji]].name + 's')
            else:
                print('boy just tried to use an invalid emoji: ' + str(reply[0].emoji))

    def start_text(self, message, time_left):
        text = 'Welcome to The Heist!\n \nTo join the heist, buy at least one item by clicking a react below \n \nCurrent items: \n'
        for item in self.heist_items:
            text += item.upper()[0] + item[1:] + 's: ' + str(self.heist_items[item]) + ' \n'
        if time_left == 1:
            text += '\nTime remaining to join: ' + str(time_left) + ' second'
        else:
            text += '\nTime remaining to join: ' + str(time_left) + ' seconds'
        return text


    async def get_vote(self, message):
        vote_counts = {}
        for react in message.reactions:
            if str(react.emoji) in self.react_list:
                vote_counts[self.react_list[str(react.emoji)]] += 1
        highest_vote = 0
        highest_voter = None
        for emoji in vote_counts:
            if vote_counts[emoji] > highest_vote:
                highest_vote = vote_counts[emoji]
                highest_voter = emoji
                vote_counts[emoji] = 0
        if highest_vote in list(vote_counts.values()):
            ties = [highest_voter]
            for emoji in vote_counts:
                if vote_counts[emoji] == highest_vote:
                    ties.append(emoji)
            return ties[random.randint(0, len(ties) - 1)]
        else:
            return highest_voter

    async def add_reacts(self, message, react_list):
        for item in item_list:
            emoji_index = None
            index = 0
            items = {}
            for i in message.server.emojis:
                if str(i) == item_list[item].emoji:
                    emoji_index = index
                    break
                index += 1
            if emoji_index is None:
                if item_list[item].emoji in react_list:
                    await client.add_reaction(message, item_list[item].emoji)
                    # items[item_list[item].emoji] = item_list[item]
            elif item_list[item].emoji in react_list:
                await client.add_reaction(message, message.server.emojis[emoji_index])
                # message.server.emojis[emoji_index] = item_list[item]


class Account(object):
    def __init__(self, user):
        self.name = user
        self.items = {}
        self.last_payday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        self.using_cipher = False

    def give_item(self, thing, amount):
        class_names = {'point': 'Point', 'high-res blue dragon': 'HighResBlueDragon', 'eli': 'Eli', 'meme': 'Meme',
                       'small smiling stone face': 'SmallSmilingStoneFace', 'gun': 'Gun', 'rope': 'Rope',
                       'cipher': 'Cipher'}
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
            print('recipient:' + str(message.mentions[0]))
            print('vendor:' + str(message.author))
            # space_counter = 0

            spaces = message_spaces(message)
            if len(spaces) >= 2:
                amount_space = spaces[1]
                item_space = spaces[2]
            else:
                await client.send_message(message.channel,
                                          'Error. You did it wrong, dumbass. The correct way is \"!give [@user] [amount] [item]\"')
                return

            if (amount_space == 0 or item_space == 0) or (
                            message.content[amount_space + 1] == ' ' or message.content[item_space + 1] == ' '):
                await client.send_message(message.channel,
                                          'Error. You did it wrong, dumbass. The correct way is \"!give [@user] [amount] [item]\"')
                return
            else:
                amount = int(message.content[amount_space + 1:item_space])
                item = message.content[item_space + 1:]
                if message.content[-1] == 's':
                    item = message.content[item_space + 1: -1]

                if item in self.items:
                    if self.items[item].amount >= amount:
                        self.give_item(item, 0 - amount)
                        recipient.give_item(item, amount)
                        if amount == 1:
                            await client.send_message(message.channel,
                                                      'Gave ' + str(amount) + ' ' + item + ' to ' + str(
                                                          message.mentions[0])[:-5])
                        else:
                            await client.send_message(message.channel,
                                                      'Gave ' + str(amount) + ' ' + item + 's to ' + str(
                                                          message.mentions[0])[:-5])
                    else:
                        await client.send_message(message.channel, 'Sorry, ' + self.name[
                                                                               :-5] + ', you don\'t have enough ' + item + 's to give.')
                else:
                    await client.send_message(message.channel, 'Sorry, ' + self.name[
                                                                           :-5] + ', you don\'t have any ' + item + 's to give.')
        else:
            await client.send_message(message.channel,
                                      'Error. You did it wrong, dumbass. The correct way is \"!give [@user] [amount] [item]\"')

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

        if (amount_space == 0 or item_space == 0) or (
                        message.content[amount_space + 1] == ' ' or message.content[item_space + 1] == ' '):
            await client.send_message(message.channel,
                                      'Error. You did it wrong, retard. The correct way is \"!buy [amount] [item]\"')
            return
        else:
            amount = int(message.content[amount_space:item_space])

            if amount < 0:
                await client.send_message(message.channel, 'Error. You can\'t buy a negative number of items')
                return

            item = message.content[item_space + 1:]
            if message.content[-1] == 's':
                item = message.content[item_space + 1: -1]

        if self.items['point'].amount >= item_list[item].value * amount:
            self.give_item('point', (0 - item_list[item].value) * amount)
            self.give_item(item, amount)
            if amount == 1:
                await client.send_message(message.channel, 'Transaction complete. You bought 1 ' + item)
            else:
                await client.send_message(message.channel,
                                          'Transaction complete. You bought ' + str(amount) + ' ' + item + 's')
        elif amount == 1:
            await client.send_message(message.channel, 'Sorry, you don\'t have enough points to buy any ' + item + 's')
        else:
            await client.send_message(message.channel,
                                      'Sorry, you don\'t have enough points to buy ' + str(amount) + ' ' + item + 's')

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

        if (amount_space == 0 or item_space == 0) or (
                        message.content[amount_space + 1] == ' ' or message.content[item_space + 1] == ' '):
            await client.send_message(message.channel,
                                      'Error. You did it wrong, retard. The correct way is \"!sell [amount] [item]\"')
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
                self.give_item('point', item_list[item].value * amount)
                self.give_item(item, 0 - amount)

                if amount == 1:
                    await client.send_message(message.channel,
                                              'Transaction complete. You sold a ' + item + ' for ' + str(
                                                  item_list[item].value) + 'points')
                else:
                    await client.send_message(message.channel, 'Transaction complete. You sold ' + str(
                        amount) + ' ' + item + 's for ' + str(item_list[item].value * amount) + ' points')
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

    async def give_random_item(self, max_number):
        item = random.choice(list(item_list.keys()))
        amount = random.randint(1, max_number)
        self.give_item(item, amount)
        return [item, amount]


# class Item(object):
#
#     def __init__(self, user):
#         self.user = user
#         self.amount = 0
#         self.value = item_list[self.name]


class Point(object):
    def __init__(self, user=None):
        self.name = 'point'
        self.emoji = '💠'
        self.user = user
        self.amount = 0
        self.value = 1

    async def use(self, message):
        if self.amount > 0:
            await client.send_message(message.channel, 'Who would you like to give this point to?')
            reply = await client.wait_for_message(timeout=300, author=message.author)
            if len(reply.mentions) > 0:
                if account_not_in_list(str(reply.mentions[0])):
                    create_account(str(reply.mentions[0]))
                get_account(str(reply.mentions[0])).give_item('point', 1)
                self.amount -= 1
                await client.send_message(message.channel, 'Gave 1 point to ' + str(reply.mentions[0])[:-5])
            else:
                await client.send_message(message.channel,
                                          'Error. Please enter an @mention of who you want to receive the point')
                return
        else:
            await client.send_message(message.channel, 'Error. You don\'t have any points')


class HighResBlueDragon(object):
    def __init__(self, user):
        self.name = 'high-res blue dragon'
        self.emoji = '<:highresbluedragon:230821355048665088>'
        self.user = user
        self.amount = 0
        self.value = 5

    async def use(self, message):
        await client.send_file(message.channel, vault_root + '/high_res_blue_dragon.jpg')
        self.user.give_item(self.name, -1)


class Eli(object):
    def __init__(self, user):
        self.name = 'eli'
        self.emoji = '<:eli:260175191563436043>'
        self.user = user
        self.amount = 0
        self.value = 25

    async def use(self, message):
        await client.send_file(message.channel, vault_root + '/' + eli_list[random.randint(0, len(eli_list))])
        self.user.give_item(self.name, -1)


class Meme(object):
    def __init__(self, user):
        self.name = 'meme'
        self.emoji = '<:guy:293564958187323393>'
        self.user = user
        self.amount = 0
        self.value = 15

    async def use(self, message):
        await client.send_message(message.channel, 'Here is your meme, ' + self.user.name[:-5])
        await self.user.send_random_image(message)
        self.user.give_item(self.name, -1)


class SmallSmilingStoneFace(object):
    def __init__(self, user):
        self.name = 'small smiling stone face'
        self.emoji = '<:smallsmilingstoneface:279073816049876992>'
        self.user = user
        self.amount = 0
        self.value = 50

    async def use(self, message):
        await client.send_file(message.channel, vault_root + '/' + rock_list[random.randint(0, len(rock_list))])
        self.user.give_item(self.name, -1)


class Gun(object):
    def __init__(self, user):
        self.name = 'gun'
        self.emoji = '🔫'
        self.user = user
        self.amount = 0
        self.value = 15

    async def use(self, message):
        await client.send_message(message.channel, 'Taking aim...')
        await asyncio.sleep(3)

        user_shot = accounts[random.randint(0, len(accounts) - 1)]

        if len(message.mentions) > 0:
            if account_not_in_list(str(message.mentions[0])):
                create_account(str(message.mentions[0]))
            user_shot = get_account(str(message.mentions[0]))

        onomatopoeia_list = ['Bam!', 'Boom!', 'Pow!', 'Kapow!', 'Kaboom!', 'Kabam!', 'Bang!', 'Pop!', 'Pew!',
                             'Baddaboom!', 'Baddabooie!']
        body_part_list = ['face', 'head', 'brain', 'left eye', 'right eye', 'mouth', 'neck', 'jaw', 'left cheek',
                          'right cheek', 'left shoulder', 'right shoulder', 'right arm', 'left arm', 'right hand',
                          'left hand',
                          'chest', 'ribcage', 'heart', 'left lung', 'right lung', 'stomach', 'kidney', 'liver',
                          'pancreas', 'bladder', 'hip', 'DICK', 'ASS', 'ASSHOLE', 'right ass cheek', 'left ass cheek',
                          'left thigh', 'right thigh', 'left leg', 'right leg', 'left kneecap', 'right kneecap',
                          'left foot', 'right foot', 'bones! oof ouch owie']

        if user_shot.name == self.user.name:
            await client.send_message(message.channel,
                                      'Bam! ' + self.user.name[:-5] + ' just shot themself in their ' + body_part_list[
                                          random.randint(0, len(body_part_list) - 1)] + '! Epic gamer fail!')
            self.user.give_item(self.name, -1)
            return

        await client.send_message(message.channel, onomatopoeia_list[
            random.randint(0, len(onomatopoeia_list) - 1)] + ' ' + self.user.name[:-5] + ' just shot ' + user_shot.name[
                                                                                                         :-5] + ' in their ' +
                                  body_part_list[random.randint(0, len(body_part_list) - 1)] + '!')
        await asyncio.sleep(2)
        await client.send_message(message.channel,
                                  self.user.name[:-5] + ' loots ' + user_shot.name[:-5] + '\'s body...')
        await asyncio.sleep(5)
        item = list(item_list.keys())[random.randint(0, len(list(item_list.keys())) - 1)]
        if user_shot.items[item].amount > 0:
            user_shot.give_item(item, -1)
            self.user.give_item(item, 1)
            await client.send_message(message.channel,
                                      self.user.name[:-5] + ' stole a ' + item + ' from ' + user_shot.name[
                                                                                            :-5] + '\'s body!')
        else:
            await client.send_message(message.channel,
                                      self.user.name[:-5] + ' tried to steal a ' + item + ' from ' + user_shot.name[
                                                                                                     :-5] + '\'s body, but they didn\'t have any!')

        self.user.give_item(self.name, -1)


class Rope(object):
    def __init__(self, user):
        self.name = 'rope'
        self.emoji = '<:rope:357349458607865857>'
        self.user = user
        self.amount = 0
        self.value = 5

    async def use(self, message):
        await client.send_message(message.channel, self.user.name[
                                                   :-5] + ' scribbles something down on a piece of paper, ties the rope into a noose, and hangs themself.')
        await asyncio.sleep(5)
        text = 'The feds come in and find ' + self.user.name[
                                              :-5] + '\'s body hanging from the ceiling. Nearby they find a note that was left behind. It reads:\n '
        message = await client.send_message(message.channel, text)
        await asyncio.sleep(4)
        text += '\n--The Last Will and Testament of ' + self.user.name[:-5] + '--'
        await asyncio.sleep(2)
        text += ' \nI hereby declare that'
        await client.edit_message(message, text)
        for item in item_list:
            if self.user.items[item].amount > 0:
                await asyncio.sleep(4)
                recipient = self.user
                while recipient.name == self.user.name:
                    recipient = accounts[random.randint(0, len(accounts) - 1)]
                amount = self.user.items[item].amount
                recipient.give_item(item, amount)
                self.user.give_item(item, -amount)
                text += '\nAll ' + str(amount) + ' of my ' + item + 's will go to ' + recipient.name[:-5]
                await client.edit_message(message, text)
        await asyncio.sleep(4)
        signature_list = ['Signing off', 'It wasn\'t just a meme after all', 'See ya', 'Fuck this shit im out',
                          'Hopefully I tied this right', 'I\'m outta here', 'Look, Ma! I\'m flyin\'!']
        text += ' \n \n' + signature_list[random.randint(0, len(signature_list) - 1)] + '\n-' + self.user.name[:-5]
        await client.edit_message(message, text)
        delete_account(self.user.name)
        await client.send_message(message.channel, self.user.name[:-5] + '\'s account has been deleted')


class Cipher(object):
    def __init__(self, user):
        self.name = 'cipher'
        self.emoji = '💻'
        self.user = user
        self.amount = 0
        self.value = 15

    async def use(self, message):
        self.user.give_item(self.name, -1)


class Cipher(object):

    def __init__(self, user):
        self.name = 'cipher'
        self.emoji = '💻'
        self.user = user
        self.amount = 0
        self.value = 15

    async def use(self, message):
        percent_throw = random.uniform(0, 100)
        target = accounts[random.randint(0, len(accounts) - 1)]
        if len(message.mentions) > 0:
            target = get_account(str(message.mentions[0]))

        await client.send_message(message.channel, 'Attempting to hack into ' + target.name[:-5] + '\'s account...')
        await asyncio.sleep(4)
        if percent_throw < 20:
            has_items = False
            for item in target.items:
                if target.items[item].amount > 0:
                    has_items = True

            if has_items is False:
                await client.send_message(message.channel, 'Success! You\'ve hacked into ' + target.name[:-5] + '\'s account, but they don\'t have any items! Epic Fail!')

            found_item = False
            while found_item is False:
                stolen_item = random.choice(list(target.items.keys()))
                if target.items[stolen_item].amount > 0:
                    found_item = True
            amount = target.items[stolen_item].amount
            self.user.give_item(stolen_item, amount)
            target.give_item(stolen_item, -amount)

            await client.send_message(message.channel, 'Success! You\'ve hacked into ' + target.name[:-5] + '\'s account and transferred ' + str(amount) + ' ' + stolen_item + 's to your account!')
        else:
            await client.send_message(message.channel, 'Hacking failed! Their defense was too strong!')

        self.user.using_cipher = False
        self.user.give_item(self.name, -1)

item_list = {'point': Point(None), 'high-res blue dragon': HighResBlueDragon(None), 'meme': Meme(None),
             'eli': Eli(None), 'small smiling stone face': SmallSmilingStoneFace(None), 'gun': Gun(None),
             'rope': Rope(None), 'cipher': Cipher(None)}

accounts = []

with open(bank_file, 'rb') as f:
    if os.path.getsize(bank_file) > 0:
        # unpickler = pickle.Unpickler(f)
        accounts = pickle.load(f)
    else:
        print('Bank file empty')

for user in accounts:
    for item in item_list:
        user.give_item(item, 0)
        user.using_cipher = False
