from bs4 import BeautifulSoup
from urllib2 import urlopen, Request
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from time import sleep
import requests
import sys
import random
import csv
import os
import mysql.connector


"""
To Run:
                        start       end
    python scraping.py 2017-03-01 2017-03-01
    date is YYYY-MM-DD
"""

# CONSTANTS
ESPN_URL = "http://scores.espn.com"

def make_soup_pbp(url, browser):
    """
        A simple helper function to make BeautifulSoup object given a url
        and browser type.
        Parameters:
            url     -- the url to be scraped
            broswer -- the browser binary type to be launched
        Returns:
            A BeautifulSoup object
    """
    browser.get(url)
    html = browser.page_source
    return BeautifulSoup(html, 'html5lib')

def get_OT_games(date,brower):
    """
    Gets all the play-by-play URLs for a given date (YYYYMMDD).
    Fair warning: ESPN doesn't have play-by-play data for all games.

    Parameters:
        date    -- the date in form YYYYMMDD
        broswer -- the browser binary type to be launched
    Returns:
        A list of strings containing the url endings to the games on
        the given date that went into overtime
    """
    soup = make_soup_pbp(ESPN_URL +
        "/mens-college-basketball/scoreboard/_/group/50/date/{0}".format(date), browser)
    scripts = soup.find_all("script")
    for script in scripts:

        if "scoreboardData" in str(script):
            games = script
            break

    gameIds = []
    links = []
    PBP_LINK = "/mens-college-basketball/playbyplay?gameId="
    searching = False
    flags = 0
    for string in str(games).split(":"):
        if "Final/" in string:
            flags += 1
        if ("gameId" in string) and flags == 2:
            stringSplit = string.split("=")
            gameId =  stringSplit[1].split(",")[0][:-1]
            if gameId not in gameIds:
                gameIds.append(gameId)
                links.append(PBP_LINK + gameId)
            searching = False
        flags = flags %4


    return links

def get_games(date, browser):
    """
    Gets all the play-by-play URLs for a given date (YYYYMMDD).
    Fair warning: ESPN doesn't have play-by-play data for all games.

    Parameters:
        date    -- the date in form YYYYMMDD
        broswer -- the browser binary type to be launched
    Returns:
        A list of strings containing the url endings to the games on
        the given date
    """
    soup = make_soup_pbp(ESPN_URL +
        "/mens-college-basketball/scoreboard/_/group/50/date/{0}".format(date), browser)
    scripts = soup.find_all("script")
    for script in scripts:

        if "scoreboardData" in str(script):
            games = script
            break

    gameIds = []
    links = []
    PBP_LINK = "/mens-college-basketball/playbyplay?gameId="
    for string in str(games).split(":"):
        if "gameId" in string:
            stringSplit = string.split("=")
            gameId =  stringSplit[1].split(",")[0][:-1]
            if gameId not in gameIds:
                gameIds.append(gameId)
                links.append(PBP_LINK + gameId)


    return links

def get_home_away(soup):
    """
        A function to determine the home and away team and their IDs
        Parameters:
            soup -- the BeautifulSoup object of the game
        Returns:
            A list of the form [team1, team2, away, home,]
    """
    header = soup.find("div",{"id":"gamepackage-header-wrap"})
    title = soup.title
    # print title
    title_list = str(title).split("vs.")
    try:
        team1 = title_list[0].split(">")[1].strip()
        team2 = title_list[1].split("Play-By-Play")[0][:-2].strip()
        print team1 + " vs. " + team2
    except:
        team1 = "Error"
        team2 = "Error"
        print title

    links = header.find_all("a",{"class":"team-name"})
    try:
        home = links[0]['href'].split("/")[-2]
        away = links[1]['href'].split("/")[-2]
    except:
        away = "Error"
        print "DIII Team"
    return [team1, team2, away, home,]

def get_play_by_play(pbp_path, browser):
    """
        Gets the play by play data for the given path
        Parameters:
            pbp_path    -- the url path for the game to be scraped
            broswer     -- the binary broswer object
        Returns:
            A nested list of the form:
            [time, team_id, description, home_score, away_score]
    """
    soup = make_soup_pbp(ESPN_URL + pbp_path, browser)
    homeAway = get_home_away(soup)
    tables = soup.find("article", { "class" :"sub-module play-by-play" }).find_all("table")
    if not tables:
        print "     No Play By Play data found!"
        return []
    rows = []
    for table in tables:
        rows += table.find_all("td")

    data = []
    data.append(homeAway)
    for i,row in enumerate(rows):
        # print row
        if "time-stamp" in str(row):
            time = row.text
            if rows[i+1].find("img") != None:
                try:
                    team = str(rows[i+1].find("img")).split("ncaa")[1].split("/")[2].split(".")[0]
                except:
                    print "Team Error"
                    team = '-1'
            else:
                team = '-1'
            text = rows[i+2].text
            score = rows[i+3].text.split("-")
            home_score = score[0].strip()
            away_score = score[1].strip()
            data.append([time, team, text, home_score, away_score])

    return data



if __name__ == '__main__':
    """
        As written this method runs a Tor Browser on a Mac.
        One Tor window must already be open and connected in order for it
        to work.
    """
    binary = '/Applications/TorBrowser.app/Contents/MacOS/firefox'
    firefox_binary = FirefoxBinary(binary)
    browser = webdriver.Firefox(firefox_binary=binary)
    # browser = webdriver.Chrome(chrome_options=chrome_options)
    try:
        START_DATE = datetime.strptime(sys.argv[1], "%Y-%m-%d")
        END_DATE = datetime.strptime(sys.argv[2], "%Y-%m-%d")
    except IndexError:
        print "I need a start and end date ('YYYY-MM-DD')."
        sys.exit()

    d = START_DATE
    delta = timedelta(days=1)
    while d <= END_DATE:
        print
        print "Getting data for: {0}".format(d.strftime("%Y-%m-%d"))

        games = get_games(d.strftime("%Y%m%d"), browser)
        print
        print "     Found: " + str(len(games)) + " games"
        print "______________________________________________"
        for game in games:

            game_id = game.lower().split("gameid=")[1]
            # I didn't feel like dealing with unicode characters
            try:
                print "Writing data for game: {0}".format(game_id)
                directory = "Games/"+d.strftime("%Y-%m-%d")
                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open(directory + "/" + game_id + ".csv", "w") as f:
                    writer = csv.writer(f, delimiter=",", quotechar='"')
                    game_data = get_play_by_play(game, browser)
                    if game_data:
                        writer.writerow([game_data[0][0],game_data[0][2],game_data[0][1],game_data[0][3]])
                        writer.writerow(["time", "team_id", "description", "h_score" , "a_score"])
                        # get_play_by_play(game, browser)
                        writer.writerows(game_data[1:])
                    else:
                        writer.writerow(["Play by play not found"])
            except UnicodeEncodeError:
                print "Unable to write data for game: {0}".format(game_id)
                print "Moving on ..."
                continue
            sleep(random.randint(0, 5))

        d += delta

         # be nice
        if random.random() < 0.5:
            print "LONG SLEEP"
            sleep(30)
        else:
            sleep(random.randint(5, 10))

    browser.quit()
