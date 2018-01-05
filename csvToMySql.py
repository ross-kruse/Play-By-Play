import csv
import glob
from datetime import datetime
import mysql.connector
from mysql.connector import Error

"""
This file reads CSV files created by scraping.py and inserts them into
a MySQL database.

Author:
    Ross Kruse
"""
ERROR_LOG = {}

def read_in_file(path):
    data = []
    with open(path, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            data.append(row)
    f.close()
    return data

def create_game_info(data, date, game_id):
    """
        This function finds the core game information and returns it
        It returns none if there is an error in the game

        Parameters:
            data    -- the nested list of scraped play-by-play data
            date    -- the date of the game
            game_id -- the game id

        Returns:
            A list of the form:
                [game_id, date, home_id, away_id, half_score_home,
                 half_score_away, final_score_home, final_score_away]
                which is the basic information of a given game
    """
    away_id = data[0][1]
    home_id = data[0][3]

    half = False
    final = False
    if home_id == "Error" or away_id == "Error":
        ERROR_LOG["Divison-III school"].append(game_id)
        return None

    i = 0
    for line in data:
        i += 1
        if line[1] == "-1":
            ERROR_LOG["Divison-III school"].append(game_id)
            return None
        if (line[0] == "0:00" and "1st half" in line[2]) and not half:
            # print line, game_id
            half_score_home = line[4]
            half_score_away = line[3]
            half = True
        elif line[0] == "0:00" and "End" in line[2] and ("Game" in line[2] or "2nd half" in line[2]):
            final_score_home = line[4]
            final_score_away = line[3]
            final = True

        # rare circumstance where the play-by-play stops in last few seconds
        elif i == len(data):
            if len(line[0]) == 4 and int(line[0].split(":")[1]) < 30 and half and final:
                final_score_home = line[4]
                final_score_away = line[3]
                final = True
            else:
                ERROR_LOG["Scraping error"].append(game_id)
                return None

    if not (half and final):
        ERROR_LOG["Scraping error"].append(game_id)
        return None
    return [int(game_id), datetime.strptime(date, '%Y-%m-%d'), int(home_id), int(away_id), int(half_score_home), int(half_score_away), int(final_score_home), int(final_score_away)]

def update_tables(game,date,game_table,event_table,assist_table,
            steal_table,name_dict):
    game_id = game.split("/")[2].split(".")[0]

    data = read_in_file(game)
    month = int(date[5:7])
    if month > 10:                          #account for fall games
        season = str(int(date[:4]) + 1)
    else:
        season = date[:4]
    if len(data) < 2:                       #this means no play-by-play exists
        ERROR_LOG["No play-by-play data"].append(game_id)
        return
    game_info = create_game_info(data, date, game_id)
    print game_info





def main():
    game_table = []
    event_table = []
    assist_table = []
    steal_table = []
    name_dict = {}

    ERROR_LOG["No play-by-play data"] = []
    ERROR_LOG["Divison-III school"] = []
    ERROR_LOG["Scraping error"] = []

    folders = glob.glob('GamesTest/*')
    date_list = []
    for folder_path in folders:
        date = folder_path.split("/")[1]
        date_list.append(datetime.strptime(date, '%Y-%m-%d'))
        game_paths = glob.glob(folder_path + '/*')
        for game in game_paths:
            update_tables(game,date,game_table,event_table,assist_table,
                        steal_table,name_dict)


    # for err in ERROR_LOG:
    #     print err, ":  " ,len(ERROR_LOG[err])
    #     print ERROR_LOG[err]




if __name__ == "__main__":
    main()
