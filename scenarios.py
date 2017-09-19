import discord
import random
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

accounts = []
item_list = {}
channel = None

client = None

heist_items = {'gun': 0, 'rope': 0, 'cipher': 0, 'toolkit': 0}
react_list = {'🔫': 'gun', '<:rope:357349458607865857>': 'rope', '💻': 'cipher', '🛠': 'toolkit',
                           '<:facewithstuckouttongueandwinking:304763680707444736>': 'talk', '🏃': 'run'}
crew = []
onomatopoeia_list = ['Bam!', 'Boom!', 'Pow!', 'Kapow!', 'Kaboom!', 'Kabam!', 'Bang!', 'Pop!', 'Pew!',
                     'Badaboom!', 'Badabooie!']
body_part_list = ['face', 'head', 'brain', 'left eye', 'right eye', 'mouth', 'neck', 'jaw', 'left cheek', 'right cheek',
                  'left shoulder', 'right shoulder', 'right arm', 'left arm', 'right hand', 'left hand', 'chest',
                  'ribcage', 'heart', 'left lung', 'right lung', 'stomach', 'kidney', 'liver', 'pancreas', 'bladder',
                  'hip', 'DICK', 'ASS', 'ASSHOLE', 'right ass cheek', 'left ass cheek', 'left thigh', 'right thigh',
                  'left leg', 'right leg', 'left kneecap', 'right kneecap', 'left foot', 'right foot',
                  'bones! oof ouch owie!']
tools_list = ['hammer', 'sledgehammer', 'screwdriver', 'bone saw', 'knife', 'nailgun', 'hammer']

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
    if heist_in_progress:
        intro = intros[random.randint(0, len(intros) - 1)]
        await intro.start()


async def start_random_room():
    if heist_in_progress:
        room = rooms[random.randint(0, len(rooms) - 1)]
        await room.start()


async def start_random_vault():
    if heist_in_progress:
        vault = vaults[random.randint(0, len(vaults) - 1)]
        await vault.start()


async def start_random_getaway():
    if heist_in_progress:
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


def get_tool():
    return tools_list[random.randint(0, len(tools_list) - 1)]


def get_random_item():
    item = 'run'
    while item == 'run' or item == 'talk':
        item = list(item_list.keys())[random.randint(0, len(list(item_list.keys())) - 1)]
        print(item)
    return item


async def fail_heist(crew_dead):
    global heist_in_progress
    heist_in_progress = False
    if crew_dead:
        await client.send_message(channel, '\nThe entire crew is DEAD! Mission failed')
    else:
        await client.send_message(channel, '\nThe crew ran away! Mission failed!')

async def win_heist(points):
    points = int(points)
    points = random.randint(points / 2, points)
    text = 'The crew got away with the money! The surving crew members are: '
    for user in crew:
        text += '\n' + user.name[:-5]
    await client.send_message(channel, text)
    await asyncio.sleep(2)
    await client.send_message(channel, '\nThe crew stole a total of ' + str(points) + ' points from the bank!')
    await asyncio.sleep(2)
    individual_points = int(points / len(crew))
    for user in crew:
        user.give_item('point', individual_points)
    await client.send_message(channel, 'Split evenly, each member gets ' + str(individual_points) + ' points! These points have been credited to each surviving crew member\'s account.')


class Talk(object):

    def __init__(self, user):
        self.name = 'talk'
        self.emoji = '<:facewithstuckouttongueandwinking:304763680707444736>'
        self.user = user
        self.amount = 0
        self.value = 0


class Run(object):

    def __init__(self, user):
        self.name = 'talk'
        self.emoji = '🏃'
        self.user = user
        self.amount = 0
        self.value = 0


class IntroRoof(object):
    async def start(self):
        if len(crew) == 0:
            await fail_heist(True)
            return

        message = await client.send_message(channel, '\nThe crew rolls up in the van and gears up next to the bank.\n')
        await asyncio.sleep(2)
        message = await client.edit_message(message,
                            message.content + '\nThe crew climbs up on to the roof. You see a ventilation shaft leading inside, and a glass skylight.')
        await add_reacts(message)
        await scenario_timer(15)
        text = message.content
        message = await client.edit_message(message, text)
        item = await get_vote(message)
        user = get_random_user()
        percent_roll = random.uniform(0, 100)
        await asyncio.sleep(2)
        if not (item == 'run' or item == 'talk'):
            if heist_items[item] == 0:
                await client.send_message(channel, 'The crew tried to use a ' + item + ', but they ran out! In the heat of the moment, they try to run!')
                item = 'run'
                await asyncio.sleep(4)
            else:
                heist_items[item] -= 1

        if item == 'gun':
            chance = 20
            await client.send_message(channel, user.name[:-5] + ' pulls out a pistol and walks up to the skylight. A security guard can be seen through the glass. ' + user.name[:-5] + ' takes aim...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, get_onomatopoeia() + ' The bullet clocks the security guard right in the ' + get_bodypart() + '!')
                await asyncio.sleep(2)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
            else:
                await client.send_message(channel, get_onomatopoeia() + ' The shot misses terribly! The guard turns around and shoots ' + user.name[:-5] + ', causing them to fall through the skylight three stories before hitting the marble floor, '
                                                                                                                   'breaking their ' + get_bodypart() + ', and killing them!')
                crew.remove(user)
        elif item == 'rope':
            chance = 75
            await client.send_message(channel, user.name[:-5] + ' takes out the rope and walks over to the skylight. They fasten the rope and start rappelling down...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, user.name[:-5] + ' makes it safely to the top floor without being seen. The rest of the crew follows.')
                await asyncio.sleep(1)
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets a bonus 10 points for their heroism!')
            else:
                await client.send_message(channel, 'While rappelling down, ' + user.name[:-5] + ' is spotted by a guard. ' + get_onomatopoeia() +  ' The guard shoots ' + user.name[:-5] + ' off of their line, causing them to fall three stories before hitting the marble floor, '
                                                                                                                   'breaking their ' + get_bodypart() + ', and killing them!')
                crew.remove(user)
        elif item == 'cipher':
            chance = 20
            await client.send_message(channel, user.name[:-5] + ' takes out their cipher and attempts to hack the bank\'s security...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, user.name[:-5] + ' breaks in to the lighting sytem of the bank, causing a black out, and allowing the crew to go in unnoticed.')
                await asyncio.sleep(1)
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets a bonus 10 points for their heroism!')
            else:
                await client.send_message(channel, user.name[:-5] + ' accidentally trips an alarm while hacking!')
                await asyncio.sleep(2)
                await client.send_message(channel, user.name[:-5] + ' is penalized 10 points for their foolishness!')
                user.give_item('point', -10)
        elif item == 'toolkit':
            chance = 75
            tool = get_tool()
            await client.send_message(channel, user.name[:-5] + ' takes out a ' + tool + ' and attempts to open the ventilation shaft...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, user.name[:-5] + ' successfully opens the vent with the ' + tool + '!')
                await asyncio.sleep(1)
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets a bonus 10 points for their heroism!')
            else:
                await client.send_message(channel, user.name[:-5] + 's hand slipped and the ' + tool + ' ran straight into their ' + get_bodypart() + ', kiling them!')
                crew.remove(user)
        elif item == 'talk':
            chance = 15
            await client.send_message(channel, user.name[:-5] + ' walks up to the skylight and sees a guard. They attempt to convince the guard that the crew is stuck and needs to be helped down...')
            await asyncio.sleep(5)
            if percent_roll < chance:
                await client.send_message(channel, 'The guard is convinced by ' + user.name[:-5] + '\'s argument, and comes on the roof to help, but as he approaches, ' + user.name[:-5] + ' mercilessly snaps his ' + get_bodypart() + ', killing the guard!')
                await asyncio.sleep(4)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
            else:
                await client.send_message(channel, 'The guard calls '+ user.name[:-5] + '\'s bluff, takes out his gun, and shoots ' + user.name[:-5] + ' right in the ' + get_bodypart() + ', killing them!')
                crew.remove(user)
        elif item == 'run':
            await client.send_message(channel, 'The crew runs away from the bank, gets in the van and leaves')
            await asyncio.sleep(2)
            await fail_heist(False)

        await asyncio.sleep(4)


class RoomSecurityOffice(object):

    async def start(self):

        if len(crew) == 0:
            await fail_heist(True)
            return

        message = await client.send_message(channel, '\nThe crew enters the security office.\n')
        await asyncio.sleep(2)
        message = await client.edit_message(message,
                            message.content + '\nInside they see an air duct and a security guard sleeping at the monitors')
        await add_reacts(message)
        await scenario_timer(15)
        text = message.content
        message = await client.edit_message(message, text)
        item = await get_vote(message)
        user = get_random_user()
        percent_roll = random.uniform(0, 100)
        await asyncio.sleep(2)
        if not (item == 'run' or item == 'talk'):
            if heist_items[item] == 0:
                await client.send_message(channel, 'The crew tried to use a ' + item + ', but they ran out! In the heat of the moment, they try to run!')
                item = 'run'
                await asyncio.sleep(4)
            else:
                heist_items[item] -= 1

        if item == 'gun':
            chance = 90
            await client.send_message(channel, user.name[:-5] + ' pulls out a pistol and carefully points the gun at the security guard\'s head...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, get_onomatopoeia() + ' The bullet clocks the security guard right in the ' + get_bodypart() + '! He didn\'t even know it was coming!')
                await asyncio.sleep(2)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
            else:
                await client.send_message(channel, get_onomatopoeia() + ' The shot misses terribly! The guard turns around and shoots ' + user.name[:-5] + ' in the ' + get_bodypart() +
                                          ', causing them to fall on the floor and spray blood on the crew!')
                await asyncio.sleep(2)
                await client.send_message(channel, user.name[:-5] + ' fires off one more round at the guard, piercing their ' + get_bodypart() + ' and killing them, right before dying themselves')
                crew.remove(user)
        elif item == 'rope':
            chance = 50
            rare_chance = 20
            await client.send_message(channel, user.name[:-5] + ' takes out the rope and attempts to sneak past the guard to get at the air duct...')
            await asyncio.sleep(4)
            if percent_roll < rare_chance:
                await client.send_message(channel, 'While sneaking past the guard, ' + user.name[:-5] + ' gets an idea! They wrap the rope around the guard\'s neck, strangling them!')
                await asyncio.sleep(2)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
            elif percent_roll < chance:
                await client.send_message(channel, user.name[:-5] + ' manages to sneak past the guard, and uses the rope to climb into the air vent. The rest of the crew follows')
                await asyncio.sleep(2)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' finds a ' + rand_item + ' in the air duct!')
            else:
                await client.send_message(channel, 'While sneaking past the guard, the guard wakes up and shoots ' + user.name[:-5] + ' right in the ' + get_bodypart() + ', making them fall to the floor!')
                await asyncio.sleep(2)
                await client.send_message(channel, user.name[:-5] + ' takes out his pistol and fires a round at the guard, piercing their ' + get_bodypart() + ' and killing them, right before dying themselves')
                crew.remove(user)
        elif item == 'cipher':
            chance = 50
            await client.send_message(channel, user.name[:-5] + ' pulls out a cipher and plugs it into the security system...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, 'The cipher worked! ' + user.name[:-5] + ' managed to unlock the door to the next room!')
                await asyncio.sleep(2)
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets a bonus 10 points for their heroism!')
            else:
                await client.send_message(channel, 'Zap! The security system detected the intrusion, and made the cipher send out a shock that hits ' + user.name[:-5] + ' stopping their heart, and killing them!')
                crew.remove(user)
        elif item == 'toolkit':
            chance = 50
            rare_chance = 20
            tool = get_tool()
            await client.send_message(channel, user.name[:-5] + ' takes out the ' + tool + ' and attempts to sneak past the guard to get at the air duct...')
            await asyncio.sleep(4)
            if percent_roll < rare_chance:
                await client.send_message(channel, 'While sneaking past the guard, ' + user.name[:-5] + ' gets an idea!' + user.name[:-5] + ' readys the ' + tool + ', swings it at the guard, and strikes his ' + get_bodypart() + ' killing him instantly!')
                await asyncio.sleep(2)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
            elif percent_roll < chance:
                await client.send_message(channel, user.name[:-5] + ' manages to sneak past the guard, and uses the ' + tool + ' to open the air vent. The rest of the crew follows')
                await asyncio.sleep(2)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' finds a ' + rand_item + ' in the air duct!')
            else:
                await client.send_message(channel, 'While sneaking past the guard, the guard wakes up and shoots ' + user.name[:-5] + ' right in the ' + get_bodypart() + ', making them fall to the floor!')
                await asyncio.sleep(2)
                await client.send_message(channel, user.name[:-5] + ' takes out his pistol and fires a round at the guard, piercing their ' + get_bodypart() + ' and killing them, right before dying themselves')
                crew.remove(user)
        elif item == 'talk':
            chance = 40
            await client.send_message(channel, user.name[:-5] + ' pulls out his gun and wakes the guard. The guard is shocked but is shut up by the gun pointed at his head.')
            await asyncio.sleep(4)
            if percent_roll < chance:
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' convinces the guard to give up a ' + rand_item + ' in exchange for sparing his life!')
                await asyncio.sleep(2)
                await client.send_message(channel, 'The crew ties up the guard before moving on')
            else:
                await client.send_message(channel, 'The guard, having nothing in his life to lose, grabs ' + user.name[:-5] + '\'s gun and shoots them in the ' + get_bodypart() + ', killing them, right before getting mowed down himself by the rest of the crew')
                crew.remove(user)
                roll = random.uniform(0, 100)
                if roll < 50:
                    user = get_random_user()
                    rand_item = get_random_item()
                    await asyncio.sleep(4)
                    user.give_item(rand_item, 1)
                    await client.send_message(channel, user.name[:-5] + ' finds a ' + rand_item + ' on the guards body!')
        elif item == 'run':
            chance = 15
            await client.send_message(channel, 'The crew makes a break for the air duct!')
            await asyncio.sleep(2)
            if percent_roll < chance:
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, 'Right before the guard wakes up, the crew manages to squeeze into the air duct and close the vent behind them. The guard just shrugs it off and goes back to sleeping')
                await asyncio.sleep(2)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' finds a ' + rand_item + ' in the air duct!')
            else:
                await client.send_message(channel, 'While everyone is trying to squeeze into the air duct, the guard pulls out his pistol and clocks ' + user.name[:-5] + ' right in the ' + get_bodypart() + ' making them fall to the ground and die!')
                crew.remove(user)

        await asyncio.sleep(4)


class VaultSafe(object):

    async def start(self):

        if len(crew) == 0:
            await fail_heist(True)
            return

        message = await client.send_message(channel, '\nThe crew finds the safe in the next room.\n')
        await asyncio.sleep(2)
        message = await client.edit_message(message,
                            message.content + '\nBesides the safe is a security guard, and he sees you! You must act quickly!')
        await add_reacts(message)
        await scenario_timer(5)
        text = message.content
        message = await client.edit_message(message, text)
        item = await get_vote(message)
        user = get_random_user()
        percent_roll = random.uniform(0, 100)
        await asyncio.sleep(2)
        if not (item == 'run' or item == 'talk'):
            if heist_items[item] == 0:
                await client.send_message(channel, 'The crew tried to use a ' + item + ', but they ran out! In the heat of the moment, they try to run!')
                item = 'run'
                await asyncio.sleep(4)
            else:
                heist_items[item] -= 1

        if item == 'gun':
            chance = 80
            await client.send_message(channel, user.name[:-5] + ' quickly slides their pistol out of their holster and fires!')
            await asyncio.sleep(2)
            if percent_roll < chance:
                await client.send_message(channel, get_onomatopoeia() + ' The bullet clocks the security guard right in the ' + get_bodypart() + '! He drops to the floor, dying instantly!')
                await asyncio.sleep(2)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
                await asyncio.sleep(3)
                await client.send_message(channel, 'The crew runs off with the safe!')
            else:
                await client.send_message(channel, user.name[:-5] + '\'s pistol jams! The guard shoots ' + user.name[:-5] + ' right in the ' + get_bodypart() + ' killing them instantly! The guard is immediately shot down by the rest of the crew.')
                crew.remove(user)
                if len(crew) > 0:
                    await asyncio.sleep(4)
                    await client.send_message(channel, 'The crew runs off with the safe!')
        elif item == 'rope':
            chance = 10
            await client.send_message(channel, user.name[:-5] + ' takes out their rope and attempts to lasso the guard!')
            await asyncio.sleep(2)
            if percent_roll < chance:
                await client.send_message(channel, get_onomatopoeia() + ' The bullet clocks the security guard right in the ' + get_bodypart() + '! He drops to the floor, dying instantly!')
                await asyncio.sleep(2)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
                await asyncio.sleep(2)
                await client.send_message(channel, 'The crew runs off with the safe!')
            else:
                await client.send_message(channel, get_onomatopoeia() + ' While ' + user.name[:-5] + ' is tying the lasso, the guard shoots them right in the ' + get_bodypart() + '!')
                crew.remove(user)
                if len(crew) > 0:
                    await asyncio.sleep(4)
                    await client.send_message(channel, 'While ' + user.name[:-5] + ' was getting shot, the rest of the crew ran off with the safe!')
        elif item == 'cipher':
            chance = 15
            await client.send_message(channel, user.name[:-5] + ' tries to do something with the cipher...')
            await asyncio.sleep(2)
            if percent_roll < chance:
                await client.send_message(channel, 'Zap! ' + user.name[:-5] + ' manages to electrocute the guard with the cipher, frying the guards ' + get_bodypart() + ', and killing him!')
                await asyncio.sleep(4)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
                await asyncio.sleep(2)
                await client.send_message(channel, 'The crew runs off with the safe!')
            else:
                await client.send_message(channel, get_onomatopoeia() + ' While ' + user.name[:-5] + ' is furiously typing on the keyboard, the guard shoots them right in the ' + get_bodypart() + ', killing them!')
                crew.remove(user)
                if len(crew) > 0:
                    await asyncio.sleep(4)
                    await client.send_message(channel, 'While ' + user.name[:-5] + ' was getting shot, the rest of the crew ran off with the safe!')
        elif item == 'toolkit':
            chance = 40
            tool = get_tool()
            await client.send_message(channel, user.name[:-5] + ' pulls out a ' + tool + ' and runs at the guard screaming!')
            await asyncio.sleep(3)
            if percent_roll < chance:
                await client.send_message(channel, get_onomatopoeia() + ' The guard misses ' + user.name[:-5] + '\'s ' + get_bodypart() + ' narrowly! ')
                await asyncio.sleep(3)
                await client.send_message(channel, user.name[:-5] + ' impales the guard\'s ' + get_bodypart() + ' with his ' + tool + ', spraying blood everywhere and killing him!')
                await asyncio.sleep(4)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
                await asyncio.sleep(2)
                await client.send_message(channel, 'The crew runs off with the safe!')
            else:
                await client.send_message(channel, get_onomatopoeia() + ' While ' + user.name[:-5] + ' is running at the guard, the guard winds up and smacks ' + user.name[:-5] + ' so hard it snaps their ' + get_bodypart() + ', killing them instantly!')
                crew.remove(user)
                if len(crew) > 0:
                    await asyncio.sleep(5)
                    await client.send_message(channel, 'While ' + user.name[:-5] + ' was getting smacked, the rest of the crew ran off with the safe!')
        elif item == 'talk':
            chance = 33
            await client.send_message(channel, 'The crew stops in their tracks, drop their weapons and put their hands up. The guard walks over to ' + user.name[:-5] + ' with his gun drawn...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, 'Once the guard gets close enough, ' + user.name[:-5] + ' quickly snatches the gun from the guards hands! Without a second thought, ' + user.name[:-5] + ' clocks the guard right in the ' + get_bodypart() + '!')
                await asyncio.sleep(4)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
                await asyncio.sleep(2)
                await client.send_message(channel, 'The crew runs off with the safe!')
            else:
                await client.send_message(channel, 'Once the guard gets close enough, ' + user.name[:-5] + ' quickly snatches the gun from the guards hands! But unknown to him, the guard has a backup pistol! The guard clocks ' + user.name[:-5] + ' right in the ' + get_bodypart() + '!')
                crew.remove(user)
                if len(crew) > 0:
                    await asyncio.sleep(5)
                    await client.send_message(channel, 'While ' + user.name[:-5] + ' was getting shot, the rest of the crew ran off with the safe!')
        elif item == 'run':
            chance = 20
            await client.send_message(channel, user.name[:-5] + ' runs at the guard screaming!')
            await asyncio.sleep(3)
            if percent_roll < chance:
                await client.send_message(channel, get_onomatopoeia() + ' The guard misses ' + user.name[:-5] + '\'s ' + get_bodypart() + ' narrowly! ')
                await asyncio.sleep(3)
                await client.send_message(channel, user.name[:-5] + ' jumps at the guard and kicks him in the ' + get_bodypart() + ', knocking them back against a wall and breaking their ' + get_bodypart() + ', killing them!')
                await asyncio.sleep(5)
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, user.name[:-5] + ' loots his body and finds a ' + rand_item + '!')
                await asyncio.sleep(2)
                await client.send_message(channel, 'The crew runs off with the safe!')
            else:
                await client.send_message(channel, get_onomatopoeia() + ' While ' + user.name[:-5] + ' is running at the guard, the guard winds up and smacks ' + user.name[:-5] + ' so hard it snaps their ' + get_bodypart() + ', killing them instantly!')
                crew.remove(user)
                if len(crew) > 0:
                    await asyncio.sleep(5)
                    await client.send_message(channel, 'While ' + user.name[:-5] + ' was getting smacked, the rest of the crew ran off with the safe!')

        await asyncio.sleep(4)


class GetawayVan(object):

    async def start(self):

        if len(crew) == 0:
            await fail_heist(True)
            return

        message = await client.send_message(channel, '\nThe crew gets in the van and starts driving!\n')
        await asyncio.sleep(2)
        message = await client.edit_message(message,
                            message.content + '\nOutside of the van you hear police sirens. You look out and see a cop car chasing the van and firing at you!')
        await asyncio.sleep(4)
        await add_reacts(message)
        await scenario_timer(15)
        text = message.content
        message = await client.edit_message(message, text)
        item = await get_vote(message)
        user = get_random_user()
        percent_roll = random.uniform(0, 100)
        await asyncio.sleep(2)
        if not (item == 'run' or item == 'talk'):
            if heist_items[item] == 0:
                await client.send_message(channel, 'The crew tried to use a ' + item + ', but they ran out! In the heat of the moment, they try to run!')
                item = 'run'
                await asyncio.sleep(4)
            else:
                heist_items[item] -= 1

        if item == 'gun':
            chance = 50
            await client.send_message(channel, user.name[:-5] + ' gets their gun out and leans out the window. ' + user.name[:-5] + ' starts spraying bullets at the cop car...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, get_onomatopoeia() + ' ' + user.name[:-5] + ' pops the cop car\'s tire, making the car wipe out and EXPLODE!')
            else:
                crew.remove(user)
                await client.send_message(channel, user.name[:-5] + ' gets shot in the ' + get_bodypart() + ' by the cop car, making them fall out of the car and die!')
                if len(crew) > 0:
                    await asyncio.sleep(3)
                    await client.send_message(channel, 'The cop car has to swerve to avoid ' + user.name[:-5] + '\'s body, giving the crew enough time to lose them!')

        elif item == 'rope':
            chance = 33
            await client.send_message(channel, user.name[:-5] + ' takes out a rope and leans out the window. ' + user.name[:-5] + ' throws the rope at the cop car...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, 'The rope gets caught in the cop car\'s tire, making it spin out!')
                await asyncio.sleep(2)
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets 10 points for their bravery!')
            else:
                await client.send_message(channel, 'A cop catches the rope and tugs at it, pulling ' + user.name[:-5] + ' out of the car!')
                await asyncio.sleep(3)
                await client.send_message(channel, user.name[:-5] + ' gets run over by the cop car, breaking their ' + get_bodypart() + ' and killing them!')
                await asyncio.sleep(3)
                await client.send_message(channel, user.name[:-5] + '\'s body causes the cop car to spin out and crash!')
                crew.remove(user)
        elif item == 'cipher':
            chance = 20
            await client.send_message(channel, user.name[:-5] + ' takes out a cipher and starts furiously typing on the keyboard...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, user.name[:-5] + ' somehow hacked the police car, taking control of it!')
                await asyncio.sleep(3)
                await client.send_message(channel, user.name[:-5] + ' uses the cop car to run over as many pedestrians as possible!')
                await asyncio.sleep(2)
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets 10 points for their bravery!')
            else:
                rand_item = get_random_item()
                user.give_item(rand_item, 1)
                await client.send_message(channel, 'While trying to hack, ' + user.name[:-5] + ' gets hit by a flying ' + rand_item + ' in the ' + get_bodypart() + ' spraying blood all over the car windows!')
                await asyncio.sleep(3)
                await client.send_message(channel, 'The van swerves into the cop car, causing it to spin out and crash!')
                crew.remove(user)
        elif item == 'toolkit':
            chance = 20
            tool = get_tool()
            await client.send_message(channel, user.name[:-5] + ' takes out a ' + tool + ', leans out the window, and gets ready to throw...')
            await asyncio.sleep(4)
            if percent_roll < chance:
                await client.send_message(channel, user.name[:-5] + ' nails the driver of the cop car in the ' + get_bodypart() + ' causing the cop car to wipe out and EXPLODE!')
                await asyncio.sleep(4)
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets 10 points for their bravery!')
            else:
                await client.send_message(channel, user.name[:-5] + ' throws the ' + tool + ' at the cop car, but it bounces back, hitting ' + user.name[:-5] + ' in the ' + get_bodypart() + ', killing them!')
                await asyncio.sleep(4)
                await client.send_message(channel, 'The ' + tool + ' did pop the cop car\'s tire, however, causing it to wipe out!')
                crew.remove(user)
        elif item == 'talk':
            chance = 10
            await client.send_message(channel, user.name[:-5] + ' slams on the brakes. The cop car rolls up next to the van and the cops get out with their guns drawn...')
            await asyncio.sleep(4)
            await client.send_message(channel, user.name[:-5] + ' says to the cops, \"I\'ve got a bomb! If you shoot me I\'ll blow you all up!\"')
            await asyncio.sleep(3)
            if percent_roll < chance:
                await client.send_message(channel, 'The cops hesitate, and the van drives away!')
                await asyncio.sleep(2)
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets 10 points for their bravery!')
            else:
                await client.send_message(channel, 'The cops proceed to mow down everyone in the car killing the whole crew!')
                await fail_heist(True)
        elif item == 'run':
            chance = 40
            await client.send_message(channel, user.name[:-5] + ' floors it, trying to outrun the cop car...')
            await asyncio.sleep(3)
            if percent_roll < chance:
                await client.send_message(channel, 'The cop car speeds up to chase the van, but starts to fishtail!')
                await asyncio.sleep(2)
                await client.send_message(channel, 'The cop car crashes into the median, barreling over it into oncoming traffic. A big rig runs straight in to the cop car and EXPLODES!')
                user.give_item('point', 10)
                await client.send_message(channel, user.name[:-5] + ' gets 10 points for their bravery!')
            else:
                await client.send_message(channel, 'The cop car catches up to the van and rams into it, causing the van to crash into a wall and EXPLODE! The whole crew is incinerated!')
                await fail_heist(True)

        await asyncio.sleep(4)

intros = [IntroRoof()]
rooms = [RoomSecurityOffice()]
vaults = [VaultSafe()]
getaways = [GetawayVan()]
