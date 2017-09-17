import discord
import random
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

accounts = []
item_list = {}
channel = None

client = None

heist_items = {'gun': 0, 'rope': 0, 'cipher': 0, 'tool': 0}
react_list = {}
crew = []
onomatopoeia_list = ['Bam!', 'Boom!', 'Pow!', 'Kapow!', 'Kaboom!', 'Kabam!', 'Bang!', 'Pop!', 'Pew!',
                     'Badaboom!', 'Badabooie!']
body_part_list = ['face', 'head', 'brain', 'left eye', 'right eye', 'mouth', 'neck', 'jaw', 'left cheek', 'right cheek',
                  'left shoulder', 'right shoulder', 'right arm', 'left arm', 'right hand', 'left hand', 'chest',
                  'ribcage', 'heart', 'left lung', 'right lung', 'stomach', 'kidney', 'liver', 'pancreas', 'bladder',
                  'hip', 'DICK', 'ASS', 'ASSHOLE', 'right ass cheek', 'left ass cheek', 'left thigh', 'right thigh',
                  'left leg', 'right leg', 'left kneecap', 'right kneecap', 'left foot', 'right foot',
                  'bones! oof ouch owie']

heist_in_progress = False


async def get_vote(message):
    vote_counts = {}
    for react in message.reactions:
        # print(len(message.reactions))
        vote_counts[str(react.emoji)] = react.count

    highest_vote = 0
    highest_voted_emoji = None
    print(vote_counts)
    for emoji in vote_counts:
        if vote_counts[emoji] > highest_vote:
            highest_vote = vote_counts[emoji]
            highest_voted_emoji = emoji
            # vote_counts[emoji] = 0

    print(highest_voted_emoji)
    ties = [highest_voted_emoji]
    for emoji in vote_counts:
        if vote_counts[emoji] == highest_vote:
            ties.append(emoji)
            # print(ties[random.randint(0, len(ties) - 1)])
            return react_list[str(ties[random.randint(0, len(ties) - 1)])]
        else:
            # print(highest_voted_emoji)
            return react_list[highest_voted_emoji]


async def add_reacts(message):
    for item in item_list:
        emoji_index = None
        index = 0
        for i in message.server.emojis:
            if str(i) == item_list[item].emoji:
                emoji_index = index
                break
            index += 1
        if emoji_index is None:
            if item_list[item].emoji in react_list:
                await client.add_reaction(message, item_list[item].emoji)
        elif item_list[item].emoji in react_list:
            await client.add_reaction(message, message.server.emojis[emoji_index])


async def start_random_intro():
    intro = intros[random.randint(0, len(intros) - 1)]
    await intro.start()


async def start_random_room():
    room = rooms[random.randint(0, len(rooms) - 1)]
    await room.start()


async def start_random_vault():
    vault = vaults[random.randint(0, len(vaults) - 1)]
    await vault.start()


async def start_random_getaway():
    getaway = getaways[random.randint(0, len(getaways) - 1)]
    await getaway.start()


def get_random_user():
    return crew[random.randint(0, len(crew) - 1)]

async def scenario_timer(seconds):
    text = '\n \n You have ' + str(seconds) + ' seconds to decide what item to use.'
    message = await client.send_message(channel, text)
    while seconds >= 0:
        await asyncio.sleep(1)
        text = '\n \n You have ' + str(seconds) + ' seconds to decide what item to use.'
        await client.edit_message(message, text)
        seconds -= 1


def get_onomatopoeia():
    return onomatopoeia_list[random.randint(0, len(onomatopoeia_list) - 1)]


def get_bodypart():
    return body_part_list[random.randint(0, len(body_part_list) - 1)]


def get_random_item():
    return list(item_list.keys())[random.randint(0, len(list(item_list.keys())) - 1)]

async def fail_heist():
    global heist_in_progress
    heist_in_progress = False
    await client.send_message(channel, '\nThe entire crew is DEAD! Mission failed')


class IntroRoof(object):
    async def start(self):
        if len(crew) == 0:
            await fail_heist()

        message = await client.send_message(channel, '\nThe crew rolls up in the van and gears up next to the bank.\n')
        await asyncio.sleep(2)
        message = await client.edit_message(message,
                            message.content + '\nThe crew rappels up on to the roof. You see a ventilation shaft leading inside, and a glass skylight.')
        await add_reacts(message)
        await scenario_timer(15)
        text = message.content
        message = await client.edit_message(message, text)
        item = await get_vote(message)
        user = get_random_user()
        percent_roll = random.uniform(0, 100)
        await asyncio.sleep(2)
        heist_items[item] -= 1
        if item == 'gun':
            chance = 20
            await client.send_message(channel, user.name[:-5] + ' pulls out a pistol and walks up to the skylight. A security guard can be seen through the glass. ' + user.name[:-5] + ' takes aim...')
            if percent_roll < chance:
                await asyncio.sleep(4)
                await client.send_message(channel, get_onomatopoeia() + ' The bullet clocks the security guard right in the ' + get_bodypart() + '!')
                await asyncio.sleep(2)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name + ' loots his body and finds a ' + rand_item + '!')
            else:
                await asyncio.sleep(4)
                await client.send_message(channel, get_onomatopoeia() + ' The shot misses terribly! The guard turns around and shoots ' + user.name[:-5] + ', causing them to fall through the skylight three stories before hitting the marble floor, '
                                                                                                                   'breaking their ' + get_bodypart() + ', and killing them!')
                crew.remove(user)
                await asyncio.sleep(4)
        elif item == 'rope':
            chance = 60
            await client.send_message(channel, user.name[:-5] + ' takes out the rope and walks over to the skylight. They fasten the rope and start rappelling down...')
            if percent_roll < chance:
                await asyncio.sleep(4)
                await client.send_message(channel, user.name[:-5] + ' makes it safely to the top floor without being seen. The rest of the crew follows.')
                await asyncio.sleep(1)
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets a bonus 10 points for their heroism!')
            else:
                await asyncio.sleep(4)
                await client.send_message(channel, 'While rappelling down, ' + user.name[:-5] + ' is spotted by a guard. ' + get_onomatopoeia() +  ' The guard shoots ' + user.name[:-5] + ' off of their line, causing them to fall three stories before hitting the marble floor, '
                                                                                                                   'breaking their ' + get_bodypart() + ', and killing them!')
                crew.remove(user)
                await asyncio.sleep(4)
        elif item == 'cipher':
            chance = 20
            await client.send_message(channel, user.name[:-5] + ' takes out their cipher and attempts to hack the bank\'s security...')
            if percent_roll < chance:
                await asyncio.sleep(4)
                await client.send_message(channel, user.namep[:-5] + ' breaks in to the lighting sytem of the bank, causing a black out, and allowing the crew to go in unnoticed.')
                await asyncio.sleep(1)
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets a bonus 10 points for their heroism!')
            else:
                await asyncio.sleep(4)
                await client.send_message(channel, user.name[:-5] + ' accidentally trips an alarm while hacking!')
                await asyncio.sleep(2)
                await client.send_message(channel, user.name[:-5] + ' is penalized 10 points for their foolishness!')
                user.give_item('point', -10)
                await asyncio.sleep(4)


intros = [IntroRoof()]
rooms = []
vaults = []
getaways = []
