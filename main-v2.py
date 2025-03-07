#!/usr/bin/env python

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup

import datetime
import json
import os
import re
import time

# Create an empty list to store all match_ids
match_ids = []

# Path to where is stored match_ids
path = os.getcwd() + r'\match_ids_input.txt'

# Open .txt file in read mode and create a list with all match_ids
with open(path, 'r') as match_ids_results:
    for line in match_ids_results.readlines():
        match_ids.append(line.strip())
        
# Create an empty list to store all dict matches
data_processed = []

def get_match_info(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    
    # Country, League, Round, Date
    tournament_info = soup.find('span', attrs={'class':'tournamentHeader__country'}).text

    # Match Date 
    match_date_scrapped = soup.find('div', attrs={'class':'duelParticipant__startTime'}).text
    match_date = datetime.datetime.strptime(match_date_scrapped, '%d.%m.%Y %H:%M').isoformat()

    # Teams
    home_team = soup.find('div', attrs={"class": re.compile('^duelParticipant__home')}).text
    away_team = soup.find('div', attrs={"class": re.compile('^duelParticipant__away')}).text

    # Results
    score = {}

    # full_time, final_result
    full_time_result = soup.find('div', attrs={'class': 'detailScore__fullTime'})
    final_result = soup.find('div', attrs={'class': 'detailScore__wrapper'})
    if full_time_result is None:
        score['final_result'] = final_result.text
    else:
        score['full_time'] = full_time_result.text.replace("(","").replace(")","")
        score['final_result'] = final_result.text

    score['match_status'] = soup.find('div', attrs={'class': 'detailScore__status'}).text

    # first_half, second_half, extra_time, penalties
    half_score_data = soup.find_all('div', attrs={'class': re.compile('^wclHeaderSection--summary')})
    for x in half_score_data:
        key = x.find_all('span')[0].text.lower()
        value = x.find_all('span')[1].text.replace(" ", "")
        score = score | {key: value}

    # ========================

    match_info = {}
    match_info_keys = soup.find_all('div', attrs={'class':re.compile('^wcl-infoLabelWrapper')})
    match_info_values = soup.find_all('div', attrs={'class':re.compile('^wcl-infoValue')})
    for k,v in zip(match_info_keys, match_info_values):
        match_info = match_info | {k.text[:-1].lower() : v.text.replace('\xa0', ' ')}


    # ========================
    # Odds

    odds = {}
    odds_data = soup.find('div', attrs={'class': 'oddsRowContent'})
    odds_labels = odds_data.find_all('span', attrs={'class': 'oddsType'})
    odss_values = odds_data.find_all('span', attrs={'class': re.compile('^oddsValue')})
    for k,v in zip(odds_labels, odss_values):
        odds = odds | {k.text : float(v.text)}



    data = {"tournament": tournament_info} | \
        {"local_datetime": match_date} | \
        {"home_team": home_team} | \
        {"away_team": away_team} | \
        {"score": score} | \
        {"match_info": match_info} | \
        {"odds": odds}

    return data
    
def get_summary(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")

    match_data = []

    data = soup.find_all('div', attrs={'class': 'smv__incident'})
    for i in data:
        match_time = i.find('div', attrs={'class': 'smv__timeBox'}).text
        
        player_out = None
        if i.find('div', attrs={'class': 'smv__incidentSubOut'}) is not None:
            player_out = i.find('div', attrs={'class': 'smv__incidentSubOut'}).text
        
        player = i.find('a', attrs={'class': 'smv__playerName'}).text

        incident = None
        if i.find('div', attrs={'class': 'smv__subIncident'}) is not None:
            incident = i.find('div', attrs={'class': 'smv__subIncident'}).text.replace('(', '').replace(')', '')

        assist = None
        if i.find('div', attrs={'class': 'smv__assist'}) is not None:
            assist = i.find('div', attrs={'class': 'smv__assist'}).text.replace('(', '').replace(')', '')

        incident_icon = None
        if i.find('div', attrs={'class': 'smv__incidentIcon'}) is not None:
            incident_icon = None if i.find('div', attrs={'class': 'smv__incidentIcon'}).text == "" else i.find('div', attrs={'class': 'smv__incidentIcon'}).text

        commentary = None
        if i.find('div', attrs={'class': ''}) is not None:
            commentary = i.find('div', attrs={'class': ''})['title'].replace('<br>', ' ').replace('<br />', ' ').replace('\n', ' ')

        # add team for each event
        if i.find_parent('div')['class'][-1][5:].startswith('home'):
            team = soup.find('div', attrs={"class": re.compile('^duelParticipant__home')}).text
        else:
            team = soup.find('div', attrs={"class": re.compile('^duelParticipant__away')}).text
        
        match_data.append({
            "time": match_time,
            "player_out": player_out,
            "player": player,
            "incident": incident,
            "assist": assist,
            "incident_icon": incident_icon,
            "commentary": commentary,
            "team": team
        })

    return match_data

def get_statistics(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    
    data = []
    for i in soup.find_all('div', attrs={'data-testid':'wcl-statistics'}):
        d = {}

        stats_name = i.find('div', attrs={'data-testid': 'wcl-statistics-category'}).text
        home_value = i.find_all('div', attrs={'data-testid': 'wcl-statistics-value'})[0].text
        away_value = i.find_all('div', attrs={'data-testid': 'wcl-statistics-value'})[1].text

        d = {
            "label": stats_name,
            "home_value": home_value,
            "away_value": away_value
        }
        
        data.append(d)

    return data
    
def get_lineup(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")

    data = {}
    data['lineup'] = {}

    try:
        data['lineup']['home_team_formation'] = soup.find_all('span', attrs={'data-testid':'wcl-scores-overline-02'})[0].text
        data['lineup']['away_team_formation'] = soup.find_all('span', attrs={'data-testid':'wcl-scores-overline-02'})[2].text
    except:
        pass

    data['lineup']['home_team'] = []
    data['lineup']['away_team'] = []

    sections = soup.find('div', attrs={'class':'lf__lineUp'})

    for section in sections:
        # Lineup players
        if section.find('div', attrs={'data-testid' : "wcl-headerSection-text"}).text == "Starting Lineups":
            home_players = section.find_all("div", attrs={'class': 'lf__side'})[0]
            away_players = section.find_all("div", attrs={'class': 'lf__side'})[-1]

            for player in home_players:
                player_dict = {}
                player_dict['jersey'] = int(player.find("span", attrs={"data-testid": "wcl-scores-simpleText-01"}).text)
                player_dict['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                player_dict['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"}).text  #['href'].split('/')[2].replace('-', ' ').title()

                player_dict['status'] = "lineup"

                data['lineup']['home_team'].append(player_dict)

            for player in away_players:
                player_dict = {}
                player_dict['jersey'] = int(player.find("span", attrs={"data-testid": "wcl-scores-simpleText-01"}).text)
                player_dict['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                player_dict['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"}).text   #['href'].split('/')[2].replace('-', ' ').title()

                player_dict['status'] = "lineup"

                data['lineup']['away_team'].append(player_dict)

        # Substituted players
        if section.find('div', attrs={'data-testid' : "wcl-headerSection-text"}).text == "Substituted players":
            home_players = section.find_all("div", attrs={'class': 'lf__side'})[0]
            away_players = section.find_all("div", attrs={'class': 'lf__side'})[-1]

            for player in home_players:
                player_dict = {}    
                player_dict['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"}).text  #['href'].split('/')[2].replace('-', ' ').title()
                try:
                    player_dict['rating'] = float(player.find_all("span", attrs={"data-testid": "wcl-scores-caption-03"})[-1].text)
                except:
                    pass
                player_dict['status'] = "Substituted player"

                data['lineup']['home_team'].append(player_dict)

            for player in away_players:
                player_dict = {}    
                player_dict['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"}).text  #['href'].split('/')[2].replace('-', ' ').title()
                try:
                    player_dict['rating'] = float(player.find_all("span", attrs={"data-testid": "wcl-scores-caption-03"})[-1].text)
                except:
                    pass
                player_dict['status'] = "Substituted player"

                data['lineup']['away_team'].append(player_dict)

        # Substitutes players
        if section.find('div', attrs={'data-testid' : "wcl-headerSection-text"}).text == "Substitutes":
            home_players = section.find_all("div", attrs={'class': 'lf__side'})[0]
            away_players = section.find_all("div", attrs={'class': 'lf__side'})[-1]

            for player in home_players:
                player_dict = {}    
                player_dict['jersey'] = int(player.find("span", attrs={"data-testid": "wcl-scores-simpleText-01"}).text)
                player_dict['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                player_dict['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"}).text  #['href'].split('/')[2].replace('-', ' ').title()
                player_dict['status'] = "Substitutes"

                data['lineup']['home_team'].append(player_dict)

            for player in away_players:
                player_dict = {}    
                player_dict['jersey'] = int(player.find("span", attrs={"data-testid": "wcl-scores-simpleText-01"}).text)
                player_dict['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                player_dict['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"}).text  #['href'].split('/')[2].replace('-', ' ').title()
                player_dict['status'] = "Substitutes"

                data['lineup']['away_team'].append(player_dict)

        # Missing Players
        if section.find('div', attrs={'data-testid' : "wcl-headerSection-text"}).text == "Missing Players":
            home_players = section.find_all("div", attrs={'class': 'lf__side'})[0]
            away_players = section.find_all("div", attrs={'class': 'lf__side'})[-1]

            for player in home_players:
                player_dict = {}    
                player_dict['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                player_dict['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"}).text    #['href'].split('/')[2].replace('-', ' ').title()
                player_dict['status'] = player.find("span", attrs={"data-testid": "wcl-scores-caption-05"}).text

                data['lineup']['home_team'].append(player_dict)

            for player in away_players:
                player_dict = {}    
                player_dict['nationality'] = player.find("img", attrs={"data-testid": "wcl-assetContainerBoxFree-XS"})["alt"]
                player_dict['name'] = player.find("a", attrs={"data-testid": "wcl-textLink"}).text    #['href'].split('/')[2].replace('-', ' ').title()
                player_dict['status'] = player.find("span", attrs={"data-testid": "wcl-scores-caption-05"}).text

                data['lineup']['away_team'].append(player_dict)

        # Coaches
        if section.find('div', attrs={'data-testid' : "wcl-headerSection-text"}).text == "Coaches":
            home_coach = section.find_all("div", attrs={'class': 'lf__side'})[0]
            away_coach = section.find_all("div", attrs={'class': 'lf__side'})[-1]

            for coach in home_coach:
                player_dict = {}  
                player_dict['nationality'] = coach.find("img", attrs={"class": re.compile("^wcl-assetContainer")})["alt"]
                player_dict['name'] = coach.find("a", attrs={"data-testid": 'wcl-textLink'}).text  #['href'].split('/')[2].replace('-', ' ').title()
                player_dict['status'] = "coach"

                data['lineup']['home_team'].append(player_dict)

            for coach in away_coach:
                player_dict = {}  
                player_dict['nationality'] = coach.find("img", attrs={"class": re.compile("^wcl-assetContainer")})["alt"]
                player_dict['name'] = coach.find("a", attrs={"data-testid": 'wcl-textLink'}).text  #['href'].split('/')[2].replace('-', ' ').title()
                player_dict['status'] = "coach"

                data['lineup']['away_team'].append(player_dict)

    return data
    
def get_commentary(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")

    comments = []

    for event in soup.find_all('div', attrs={'data-testid': 'wcl-commentary'}):
        try:
            minute = event.find('strong', attrs={'data-testid': 'wcl-scores-simpleText-02'}).text.replace("'", "")
        except:
            minute = '0'
    
        try:
            comment = event.find('div', attrs={'class': re.compile('^wcl-general_')}).text
        except:
            pass
        try:
            comment = event.find('div', attrs={'class': re.compile('^wcl-highlighted_')}).text
        except:
            pass
        try:
            comment = event.find('div', attrs={'class': re.compile('^wcl-live_')}).text
        except:
            pass

        comments.append((minute, comment))
        comments.reverse()
        
    return comments
    
def get_report(driver):
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    
    ps = soup.find('div', attrs={'class': 'fsNewsArticle__content'})
    return ps.text.strip().split('\n')[-1].split(': ')[-1]
    
def main():
    # Open Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')  # Last I checked this was necessary.
    options.add_argument('--log-level=3') # Remove information from console

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    x = 0
    for match_id in match_ids:
        print('Current match: ' + str(match_id) + '\t' + 'Remaining: ' + str(len(match_ids) - 1 - x))

        url = 'https://www.flashscore.com/match/' + match_id + "/#match-summary"

        driver.get(url)
        time.sleep(1)

        # Accept GDPR
        try:
            driver.find_element(by='id', value='onetrust-accept-btn-handler').click()
        except:
            pass

        # Click on the Match tab to start scrapping
        try:
            driver.find_element(by='xpath', value="//a[@href='#/match-summary']").click()
            time.sleep(1.5)
        except:
            pass

        match_data = {}
        match_data = match_data | get_match_info(driver)

        match_data['events'] = get_summary(driver)

        # Match statistics
        match_data['statistics'] = {}
        driver.find_element(by='xpath', value="//a[@href='#/match-summary/match-statistics']").click()
        time.sleep(1.5)
        match_data['statistics']['full_time'] = get_statistics(driver)

        driver.find_element(by='xpath', value="//a[@href='#/match-summary/match-statistics/1']").click()
        time.sleep(1.5)
        match_data['statistics']['1st_half'] = get_statistics(driver)

        driver.find_element(by='xpath', value="//a[@href='#/match-summary/match-statistics/2']").click()
        time.sleep(1.5)
        match_data['statistics']['2nd_half'] = get_statistics(driver)
     
        try:
            driver.find_element(by='xpath', value="//a[@href='#/match-summary/match-statistics/3']").click()
            time.sleep(1.5)
            match_data['statistics']['extra_time'] = get_statistics(driver)
        except:
            pass

        # Players
        driver.find_element(by='xpath', value="//a[@href='#/match-summary/lineups']").click()
        time.sleep(1.5)
        match_data = match_data | get_lineup(driver) 

        # Match comentary
        try:
            driver.find_element(by='xpath', value="//a[@href='#/match-summary/live-commentary']").click()
            time.sleep(1.5)
            match_data['commentary'] = get_commentary(driver)
        except:
            pass   
        
        # Man of the match
        try:
            driver.find_element(by='xpath', value="//a[@href='#/report']").click()
            time.sleep(1.5)
            match_data['man_of_the_match'] = reports(driver)
        except:
            pass

        data_processed.append(match_data)
        x += 1

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    with open(os.getcwd() + r'\processed' + '\\' + str(yesterday.date()) + '.json', 'w') as json_file:
        json.dump(data_processed, json_file)