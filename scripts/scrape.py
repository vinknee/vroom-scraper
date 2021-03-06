#!/usr/bin/env python3

import argparse
import os
import re
import requests

from collections import defaultdict

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--urls', help='file for vroom urls to scrape', default=os.getenv('HOME') + '/vroom_urls.txt')
    parser.add_argument('--mg_url', help='base mailgun api url', default=os.getenv('MG_URL'))
    parser.add_argument('--mg_key', help='mailgun api key', default=os.getenv('MG_KEY'))
    parser.add_argument('--emails', help='email for notifications')
    parser.add_argument('--affirmative', help='send email even if cars are not available', action='store_true')

    args = parser.parse_args()

    #slurp file
    f = open(args.urls, 'r')
    urls = f.read().split('\n')
    
    status = defaultdict(list)

    for u in urls:
        if u == '': continue
        resp = requests.get(u)
        
        if re.findall('Sale Pending', resp.text, re.IGNORECASE):
            status['Sale Pending'].append(u)
        elif re.findall('Car Not Found', resp.text, re.IGNORECASE):
            status['Not Found! Delisted?'].append(u)
        elif re.findall('Available Soon', resp.text, re.IGNORECASE):
            status['Not Available Yet'].append(u)
        elif re.findall('Start Purchase', resp.text, re.IGNORECASE):
            status['Available for purchase!'].append(u)
        else:
            status['Unkown!'].append(u)

    msg = ""
    # statuses are in alphabetical importance to me: Available -> Not Available Yet -> Sale Pending -> Unknown
    for s in sorted(status.keys()):
        for u in status[s]: 
            msg += f"{s}: {u}\n" 


    if args.affirmative or len(status['Available for purchase!']):
        ret = requests.post(f"https://api.mailgun.net/v3/{args.mg_url}/messages", auth=("api", args.mg_key), 
            data={
                "from"      : f"Vroom Watcher <mailgun@{args.mg_url}>",
                "to"        : args.emails.split(','),
                "subject"   : "Car Updates!",
                "text"      : msg
            })
    
    print(msg)

if __name__ == "__main__":
    main()
