from vrage_api.vrage_api import VRageAPI
import discord, asyncio
from discord import app_commands

intents = discord.Intents().all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

with open('settings.txt', 'r') as f:
    data = f.readlines()
for line in range(len(data)):
    data[line] = data[line].replace('\n', '')

settings = {}

for line in data:
    try:
        settings[line[:line.find('=')]] = int(line[line.find('=')+1:])
    except:
        settings[line[:line.find('=')]] = line[line.find('=')+1:]

settings['url'],settings['port']=settings['url'].split(':')

api = VRageAPI(url=f'http://{settings["url"]}:{settings["port"]}', token=settings["SETokenID"])

print(settings)

key = '/se'
levels = {
    0: 'Player',
    1: 'Scripter',
    2: 'Moderator',
    3: 'Space Master',
    4: 'Admin',
    5: 'Owner'
}

with open('permissions.txt', 'r') as f:
    pdata = f.readlines()
    pdata.remove('#discordID:PermissionLevel\n')
for line in range(len(pdata)):
    pdata[line] = pdata[line].replace('\n', '')
user_permissions = {}
for line in pdata:
    user_permissions[int(line.split(':')[0])] = int(line.split(':')[1])
print(user_permissions)

def is_allowed(authorID,req_permission_level):
    if authorID in user_permissions:
        return user_permissions[authorID] >= req_permission_level
    return False

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.id != settings["channelID"]:
        return
    api.send_chat_message(f'{message.author}: {message.content}')

@tree.command(name = "players", description = "Player List", guild=discord.Object(id=settings["serverID"]))
async def players(interaction:discord.ui.text_input):
    players = api.get_players()['data']['Players']
    online_players = {}
    for player in players:
        if player['Ping'] != -1:
            online_players[player['SteamID']]={'Name: ':player['DisplayName'],'Faction: ':player['FactionName'],'Role: ':levels[player['PromoteLevel']],'Ping: ':player['Ping']}
    
    sendmessage = ''
    for ID in online_players:
        for value in online_players[ID]:
            sendmessage += f'{value}{online_players[ID][value]}\n'
        sendmessage+='\n'
    if sendmessage == '':
        sendmessage = 'No Players Active'

    await interaction.response.send_message(embed=discord.Embed(title='Players', description=sendmessage))


@tree.command(name="grids", description="Grid List", guild=discord.Object(id=settings["serverID"]))
async def grids(interaction:discord.ui.text_input):
    grids = api.get_grids()['data']['Grids']

    usable_grid_data ={}
    for grid in grids:
        if is_allowed(interaction.user.id,3):
            usable_grid_data[grid['EntityId']]={'Name: ': grid['DisplayName'], 'Size: ': grid['GridSize'], 'Blocks: ': grid['BlocksCount'], 'Owner: ': grid['OwnerDisplayName'],'ID: ':grid['EntityId']}
        else:
            usable_grid_data[grid['EntityId']]={'Name: ':grid['DisplayName'],'Size: ':grid['GridSize'],'Blocks: ':grid['BlocksCount'],'Owner: ':grid['OwnerDisplayName']}

    sendmessage = ''
    for grid in usable_grid_data:
        for value in usable_grid_data[grid]:
            sendmessage += f'{value}{usable_grid_data[grid][value]}\n'
        sendmessage += '\n'
    if sendmessage == '':
        sendmessage = 'No Grids'

    await interaction.response.send_message(embed=discord.Embed(title='Grids', description=sendmessage))

async def ch_pr():
    await client.wait_until_ready()

    player_names = []
    players = api.get_players()['data']['Players']
    for player in players:
        if player['Ping'] != -1 and player['DisplayName'] not in player_names:
            player_names.append(player['DisplayName'])
    while not client.is_closed():
        try:
            players = api.get_players()['data']['Players']
            presence = None

        except:
            presence = 'Server Offline'

        if presence != 'Server Offline':
            online_players = 0
            current_players = []
            for player in players:
                if player['Ping'] != -1:
                    online_players += 1
                    current_players.append(player['DisplayName'])
                    if player['DisplayName'] not in player_names:
                        player_names.append(player['DisplayName'])
                        await client.get_channel(settings['channelID']).send(embed=discord.Embed(color=0x00ff00,description=f'{player["DisplayName"]} has joined'))

            for name in player_names:
                if name not in current_players:
                    await client.get_channel(settings['channelID']).send(embed=discord.Embed(color=0xff0000, description=f'{name} has disconnected'))
                    player_names.remove(name)
                    online_players -= 1
                    
            presence = f'{online_players} Players Online'
        await client.change_presence(activity=discord.Game(name=presence))
        await asyncio.sleep(60)

async def send_server_chat():
    global activities

    await client.wait_until_ready()
    
    message_history = api.get_chat()['data']['Messages']
    
    while not client.is_closed():
        try:
            new_messages = api.get_chat()['data']['Messages']
            for message in new_messages:
                if message not in message_history and message["DisplayName"] != 'Good.bot':
                    message_history.append(message)
                    sendable_message = f'{message["DisplayName"]}: {message["Content"]}'
                    await client.get_channel(settings["channelID"]).send(sendable_message)
        except:
            pass

        await asyncio.sleep(10)

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=settings['serverID']))
    client.loop.create_task(send_server_chat())
    client.loop.create_task(ch_pr())
    print("Ready!")

client.run(settings['DiscordToken'])
