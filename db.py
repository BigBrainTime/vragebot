import sqlite3, time, steamapi
from operator import itemgetter

connection = sqlite3.connect('database/vrage.db')
cursor = connection.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS linked(SteamID INT,DiscordID INT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS timelog(SteamID INT,Time INT, first_login INT, last_login INT)''')
connection.commit()

def create_link(steamID,disID):
    if not bool(cursor.execute(f"SELECT EXISTS(SELECT * FROM linked WHERE SteamID = ? AND DiscordID = ?)", (steamID, disID)).fetchone()[0]):
        cursor.execute('''INSERT INTO linked VALUES(?,?)''',(steamID, disID))
        connection.commit()

def add_time(steamID):
    now_time = int(time.time())
    if not bool(cursor.execute(f"SELECT EXISTS(SELECT * FROM timelog WHERE SteamID = ?)", (steamID,)).fetchone()[0]):
        cursor.execute('''INSERT INTO timelog VALUES(?,?,?,?)''',
                       (steamID, 0, now_time, now_time))

    curtime = cursor.execute(
        '''SELECT * FROM timelog WHERE SteamID = ?''', (steamID,)).fetchone()[1]
    cursor.execute('''UPDATE timelog SET Time = ?, last_login = ? WHERE SteamID = ?''',(curtime+1,now_time,steamID))
    connection.commit()

def get_time(ID):
    if not bool(cursor.execute(f"SELECT EXISTS(SELECT * FROM linked WHERE DiscordID = ? OR SteamID = ?)", (ID,ID)).fetchone()[0]):
        return False
    steamID = cursor.execute(
        f"SELECT SteamID FROM linked WHERE DiscordID = ? OR SteamID = ?", (ID, ID)).fetchone()[0]
    return cursor.execute(f"SELECT * FROM timelog WHERE SteamID = ?", (steamID,)).fetchone()

def get_player_history():
    player_count = len(cursor.execute('''SELECT * FROM linked''').fetchall())
    time_data = sorted(cursor.execute("SELECT * FROM timelog").fetchall(),key=itemgetter(1))
    top_players = {}
    for player in time_data[:3]:
        top_players[steamapi.get_name(player[0])]=player[1]
    total_time = sum(map(itemgetter(1),time_data))
    top_time = sum(top_players.values())
    return player_count,top_players, total_time, top_time