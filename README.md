# Python script to scrape Flashscore match

Make sure to have Python v3.9+ installed

## Environment setup
1. Clone/Download the repo
2. Open terminal and cd in that repo
3. Create a virtual environment
run ```python -m venv venv```
4. Install requirements
run ```pip install -r requirements.txt```
5. Activate environment
In windows run ```.\_venv\Scripts\activate```
In Linux run ```source venv/bin/activate```

## Usage
Go to www.flashscore.com and make a list with all the matches you want to scrape
Copy the match ID in the **match_ids_input.txt** file

**Note:** Match ID can be found in the url link: https://www.flashscore.com/match/**l4DvtYcA**/

run ```python .\main-v2.py```
Data will be saved in **\\processed\\** in JSON format **<YYYY-MM-DD>**