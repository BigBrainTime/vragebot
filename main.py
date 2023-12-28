from vrage_api.vrage_api import VRageAPI
import discord, asyncio,steamapi, random,uuid,db
from discord import app_commands
from math import ceil
from datetime import datetime

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

Active_codes = {}

def is_allowed(authorID,req_permission_level):
    if authorID in user_permissions:
        return user_permissions[authorID] >= req_permission_level
    return False

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.id != settings["channelID"]:
        return
    api.send_chat_message(f'{message.author}: {message.content}')

@tree.command(name = "stop", description = "stop_server", guild=discord.Object(id=settings["serverID"]))
async def stop(interaction:discord.ui.text_input):
    if is_allowed(interaction.user.id,4):
        api.stop_server()
        await interaction.response.send_message(embed=discord.Embed(title='Stop', description='Server Stopped - Contact Owner for reboot'))
    else:
        await interaction.response.send_message(embed=discord.Embed(title='Stop', description='Acces Denied'))


@tree.command(name="clear_floating", description="Clear All Floating Objects", guild=discord.Object(id=settings["serverID"]))
async def clear_objects(interaction: discord.ui.text_input):
    if not is_allowed(interaction.user.id, 3):
        return await interaction.response.send_message(embed=discord.Embed(title='Clear Objects', description='Acces Denied'))
    
    await interaction.response.send_message(embed=discord.Embed(title='Clear Objects', description='Please Wait'))
    objects = api.get_floating_objects()['data']['FloatingObjects']
    if len(objects) == 0:
        return await interaction.edit_original_response(embed=discord.Embed(title='Clear Objects', description=f'No Objects To Clear'))
    for delay in (60,50,40,30,20,10):
        api.send_chat_message(f'CLEARING ALL FLOATING OBJECTS IN {delay} SECONDS!')
        await interaction.edit_original_response(embed=discord.Embed(title='Clear Objects', description=f'Clearing In {delay} Seconds'))
        await asyncio.sleep(10)
    api.send_chat_message(f'CLEARING ALL FLOATING OBJECTS NOW!')
    await interaction.edit_original_response(embed=discord.Embed(title='Clear Objects', description=f'Clearing Now'))
    for object in objects:
        api.delete_floating_object(object['EntityId'])
    await interaction.edit_original_response(embed=discord.Embed(title='Clear Objects', description=f'{len(objects)} Objects Cleared'))
    

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

@tree.command(name="delgrid", description="Delete Grid", guild=discord.Object(id=settings["serverID"]))
async def delgrid(interaction:discord.ui.text_input,id:str):
    if not is_allowed(interaction.user.id, 2):
        return await interaction.response.send_message(embed=discord.Embed(title='Del Grid', description='Acces Denied'))
    
    api.delete_grid(id)
    await interaction.response.send_message(embed=discord.Embed(title='Del Grid', description='Grid Deleted'))

@tree.command(name="link", description="link steam and discord accounts", guild=discord.Object(id=settings["serverID"]))
async def link(interaction:discord.ui.text_input):
    verify_code=str(uuid.uuid1())
    Active_codes[verify_code]= interaction.user.id
    await interaction.response.send_message(f'Enter this code in game within 5 minutes to link accounts\n\n/L{verify_code}', ephemeral=True)
    await asyncio.sleep(300)
    try:
        del Active_codes[verify_code]
    except:
        pass #Code Redeemed

@tree.command(name="alltime", description="Shows all players time on server", guild=discord.Object(id=settings["serverID"]))
async def showalltime(interaction:discord.ui.text_input):
    data = db.get_player_history()
    msg = f'{data[0]} players have played {data[2]} minutes, the top players putting in {data[3]} minutes.\n\n'
    for player in data[1]:
        msg += f'{player}: {data[1][player]}'
    embed = discord.Embed(title=f'{data[0]} Players have joined',description=msg)
    await interaction.response.send_message(embed=embed)

@tree.command(name="time", description="Shows your time on the server, REQURES /link FIRST FOR DISCORD MEMBER", guild=discord.Object(id=settings["serverID"]))
async def showtime(interaction:discord.ui.text_input, member:str=None):
    if member is None:
        member = interaction.user.id
    data = db.get_time(int(member))
    if data == False:
        return await interaction.response.send_message('No linked account')
    name = steamapi.get_name(data[0])
    first_login = datetime.utcfromtimestamp(data[2]).strftime('%Y-%m-%d')
    last_login = datetime.utcfromtimestamp(data[3]).strftime('%Y-%m-%d')
    embed = discord.Embed(title=name,description=f'Minutes: {data[1]}\nFirst Login(UTC): {first_login}\nLast Login(UTC): {last_login}')
    await interaction.response.send_message(embed=embed)

gridsperpage = 5
@tree.command(name="grids", description="Grid List", guild=discord.Object(id=settings["serverID"]))
async def grids(interaction:discord.ui.text_input,page:int):
    await interaction.response.send_message(embed=discord.Embed(title='Grids', description='Please Wait'))
    grids = api.get_grids()['data']['Grids']
    usable_grid_data ={}
    if page > ceil(len(grids)/gridsperpage):
        page = ceil(len(grids)/gridsperpage)
    elif page < 1:
        page = 1
    for grid in grids[gridsperpage*(page-1):gridsperpage*page]:
        if is_allowed(interaction.user.id,2):
            usable_grid_data[grid['EntityId']]={'Name: ': grid['DisplayName'], 'Size: ': grid['GridSize'], 'Blocks: ': grid['BlocksCount'], 'Owner: ': grid['OwnerDisplayName'],'ID: ':grid['EntityId']}
        else:
            usable_grid_data[grid['EntityId']]={'Name: ':grid['DisplayName'],'Size: ':grid['GridSize'],'Blocks: ':grid['BlocksCount'],'Owner: ':grid['OwnerDisplayName']}

    sendmessage = ''
    for grid in usable_grid_data:
        tempsendmessage=''
        for value in usable_grid_data[grid]:
            tempsendmessage += f'{value}{usable_grid_data[grid][value]}\n'
        if len(sendmessage+f'{tempsendmessage}\n') < 4096:
            sendmessage += f'{tempsendmessage}\n'

    if sendmessage == '':
        sendmessage = 'No Grids'

    title = f'Grids:({len(usable_grid_data)}/{len(grids)}) Page:({page}/{ceil(len(grids)/gridsperpage)})'
    await interaction.edit_original_response(embed=discord.Embed(title=title, description=sendmessage))

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
            current_players = []
            for player in players:
                if player['Ping'] != -1:
                    current_players.append(player['DisplayName'])
                    db.add_time(player['SteamID'])
                    if player['DisplayName'] not in player_names:
                        player_names.append(player['DisplayName'])
                        embed = discord.Embed(
                            color=0x00ff00, description=f'{player["DisplayName"]} has joined')
                        embed.set_thumbnail(
                            url=steamapi.get_image(player['SteamID']))
                        await client.get_channel(settings['channelID']).send(embed=embed)

            for name in player_names:
                if name not in current_players:
                    embed = discord.Embed(color=0xff0000, description=f'{name} has disconnected')
                    await client.get_channel(settings['channelID']).send(embed=embed)
                    player_names.remove(name)
                    
            presence = f'{(len(current_players))}/{db.get_player_history()[0]} Online'
        await client.change_presence(activity=discord.Game(name=presence))
        await asyncio.sleep(60)

async def send_server_chat():
    global activities

    await client.wait_until_ready()
    
    message_history = api.get_chat()['data']['Messages']
    
    while not client.is_closed():
        new_messages = api.get_chat()['data']['Messages']
        for message in new_messages:
            if message not in message_history and message["DisplayName"] != 'Good.bot':
                message_history.append(message)
                sendable_message = f':computer:{message["DisplayName"][1:]}: {message["Content"]}'
                if message["Content"].startswith('/L'):
                    code = message["Content"][2:]
                    if code in Active_codes:
                        db.create_link(message['SteamID'], Active_codes[code])
                        user = await client.fetch_user(Active_codes[code])
                        msg = f'You have linked to **{steamapi.get_name(message["SteamID"])}**'
                        del Active_codes[code]
                        await user.send(msg)
                else:
                    await client.get_channel(settings["channelID"]).send(sendable_message)

        await asyncio.sleep(10)

announcements = ('https://discord.gg/NK9RZUc','ASTEROID INBOUND')
async def server_broad():
    await client.wait_until_ready()
    
    while not client.is_closed():
        await asyncio.sleep(3600)
        api.send_chat_message(f"{random.choice(announcements)}")

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=settings['serverID']))
    client.loop.create_task(send_server_chat())
    client.loop.create_task(ch_pr())
    client.loop.create_task(server_broad())
    await client.wait_until_ready()
    print("Ready!")

client.run(settings['DiscordToken'])
