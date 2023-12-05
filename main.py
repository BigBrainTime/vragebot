from vrage_api.vrage_api import VRageAPI
import discord, asyncio
from discord import app_commands

intents = discord.Intents().all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

with open('Token.txt', 'r') as f:
    TOKEN = f.read()

with open('SEToken.txt', 'r') as f:
    SETOKEN = f.read()

with open('channel.txt', 'r') as f:
    serverID,channelID = list(map(int,f.readlines()))

with open('url.txt', 'r') as f:
    url,port = f.read().split(':')

api = VRageAPI(url=f'http://{url}:{port}', token=SETOKEN)


key = '/se'
levels = {
    0: 'Player',
    1: 'Scripter',
    2: 'Moderator',
    3: 'Space Master',
    4: 'Admin',
    5: 'Owner'
}

user_permissions = {
    371422034544295937:4,#Rogue
    311701516652380160:4,#Lucky
    342001099190042626:5 #Me
}

def is_allowed(authorID,req_permission_level):
    if authorID in user_permissions:
        return user_permissions[authorID] >= req_permission_level
    return False

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.id != channelID:
        return

@tree.command(name = "players", description = "Player List", guild=discord.Object(id=serverID))
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


@tree.command(name="grids", description="Grid List", guild=discord.Object(id=serverID))
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
            online_players = 0
            current_players = []
            for player in players:
                if player['Ping'] != -1:
                    online_players += 1
                    current_players.append(player['DisplayName'])
                    if player['DisplayName'] not in player_names:
                        player_names.append(player['DisplayName'])
                        await client.get_channel(channelID).send(embed=discord.Embed(title='Join',description=f'{player["DisplayName"]} has joined'))

            for name in player_names:
                if name not in current_players:
                    await client.get_channel(channelID).send(embed=discord.Embed(title='Disconnect', description=f'{name} has disconnected'))
                    player_names.remove(name)
                    
            presence = f'{online_players} Players Online'
        except:
            presence = 'Server Offline'
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
                if message not in message_history:
                    message_history.append(message)
                    sendable_message = f'{message["DisplayName"]}: {message["Content"]}'
                    await client.get_channel(channelID).send(sendable_message)
        except:
            pass

        await asyncio.sleep(10)

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=serverID))
    client.loop.create_task(send_server_chat())
    client.loop.create_task(ch_pr())
    print("Ready!")

client.run(TOKEN)
