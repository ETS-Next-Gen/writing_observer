'''
A thin, async wrapper to languagetool
'''

import asyncio
import inspect
import aiohttp
import sys
import json
import os
  
#import categories to add to languagetool outputs
fn = os.path.dirname(os.path.abspath(__file__))
fn += '/languagetool_rulemapping.json'
fo = open(fn, "r")
jsonContent = fo.read()
ruleInfo = json.loads(jsonContent)
fo.close()

session = None

# build a table mapping all non-printable characters to None
NOPRINT_TRANS_TABLE = {
    i: None for i in range(0, sys.maxunicode + 1) if not chr(i).isprintable()
}

def make_printable(s):
    """Replace non-printable characters in a string."""

    # the translate method on str removes characters
    # that map to None from the string
    return s.translate(NOPRINT_TRANS_TABLE)

async def check(language, text):
    '''
    Takes a language (e.g. `en-US`), and a text.

    Returns a JSON object of the LanguageTool spell / grammar
    check
    '''

    global session
    if session is None:
        session = aiohttp.ClientSession()
    if inspect.iscoroutinefunction(session):
        session = await session

    query = {
        'language': language,
        'text': text
    }
    resp = await session.post(
        'http://localhost:8081/v2/check',
        data=query
    )

    return await resp.json()

async def processText(event, text):
    '''
    This adds up time intervals between successive timestamps. If the interval
    goes above some threshold, it adds that threshold instead (so if a student
    goes away for 2 hours without typing, we only add e.g. 5 minutes if
    `time_threshold` is set to 300.
    '''

    print('Trying language tool')
    matches = []
    try:
        result = await check('en-US', make_printable(text.replace('\n','<p>')).replace('<p>','\n'))
        for match in result['matches']:
            newmatch = match
            try:
                ruleId = match['rule']['id']
                if ruleId in ruleInfo.keys():
                    if 'subId' in match['rule']:
                        ruleSubId = match['rule']['subId']
                        if ruleSubId in ruleInfo[ruleId]:
                            label = ruleInfo[ruleId][ruleSubId][0]
                            detail = ruleInfo[ruleId][ruleSubId][1]
                        else:
                            print('ruleSubID not in ruleInfo for ruleID ' + ruleId, match)
                    elif 'nil' in ruleInfo[ruleId]:
                        label = ruleInfo[ruleId]['nil'][0]
                        detail = ruleInfo[ruleId]['nil'][1]
                    else:
                        print('no valid match for ruleID ' + ruleID)
                    newmatch['label'] = label
                    newmatch['detail'] = detail
                    matches.append(newmatch)
                else:
                    print('ruleId not in match',match)
            except Exception as e: 
                print('Error a',e)                    
           
    except Exception as e: 
        print('Error b', e)
        
    return matches

