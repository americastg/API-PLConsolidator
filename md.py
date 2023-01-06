import datetime
import os
import requests
import json

with open('settings.json', 'r') as f:
    config = json.load(f)


def get_token():
    response = requests.post(
        url=f"{config['base_url']}:{config['token_port']}/connect/token", 
        data= {
            'grant_type': 'client_credentials',  # do not change
            'scope': 'mdapi4',    # do not change
            'client_id': config['cred_mdapi']['client_id'],
            'client_secret': config['cred_mdapi']['client_secret']})
    response.raise_for_status()
    return response.json()['access_token']


def get_symbol_info(symbol: str):
    if os.environ.get('md_token') == None:
        os.environ['md_token'] = get_token()
        
    response = requests.get(
        url=f"{config['base_url']}:{config['mdapi_port']}/api/instruments/{symbol}",
        headers={'Authorization': 'Bearer ' + os.environ['md_token']})

    if response.status_code != 200:
        print(f'{datetime.now():%H:%M:%S}: Error {response.status_code}')

    return response.json()