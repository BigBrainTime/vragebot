import requests,json,os,shutil

DIR = os.getcwd()

with open(os.path.join(DIR,'steamapikey.txt'),'r') as k:
    key = k.read()

def get_image(id):
    return json.loads(requests.get(
        f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={key}&steamids={id}").text)['response']['players'][0]['avatarfull']

def get_name(id):
    return json.loads(requests.get(
        f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={key}&steamids={id}").text)['response']['players'][0]['personaname']
