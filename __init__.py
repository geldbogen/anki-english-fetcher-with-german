from json import JSONDecodeError
from aqt import mw
from anki.hooks import addHook
import requests
import os

global editorWindow

english_field="english word"
english_definitions_field="english definition"
german_translation_field="german translation"
german_translation_field_alternative="alternative translations"
pronunciation_field="pronunciation (sound)"
etymology_field="etymology"
difficulty_score_field="difficulty/frequency"
slang_information_field="slang information"
slang_example_field="slang example sentences"
slang_url_field="urbandictionary-url"
example_sentences_entry="example sentences"
examples_prepared_field="prepared sentences"

# import the addon's config file 
config = mw.addonManager.getConfig(__name__)

#get the windows user name
windowsusername=os.getlogin()

# get the windows user name
ankiusername=config["Anki username"]

# get key for ger-eng API 
petapro_api_key=config["Petapro API Key (https://rapidapi.com/petapro/api/linguatools-translate)"]

# get key and ID for Oxford API 
ox_key=config["Oxford Dictionary API Key (https://developer.oxforddictionaries.com/)"]
ox_id=config["Oxford Dictionary API ID (https://developer.oxforddictionaries.com/)"]

# get UK or US:
if config["UK or US"]=="UK":
    uk_or_us="en-gb"
else:
    uk_or_us="en-us"

# get key for twinword API (difficulty)
twinword_key=config["Twinword language scoring API Key (https://rapidapi.com/twinword/api/twinword-text-analysis-bundle)"]

# get key for Urbandictionary API 
urban_key=config["Urban Dictionary API Key (https://rapidapi.com/community/api/urban-dictionary)"]

def fill_the_fields(flag):
    global editorWindow
    n=editorWindow.editor.note

    search_string=mw.col.media.strip(n[english_field])

    #API 1 - german-english translation
    try:

        url = "https://petapro-translate-v1.p.rapidapi.com/"

        params = {"query":search_string,"langpair":"en-de"}

        headers = {
        'x-rapidapi-host': "petapro-translate-v1.p.rapidapi.com",
        'x-rapidapi-key': petapro_api_key
        }
        r=requests.get(url=url,params=params,headers=headers)
        r=r.json()
        n[german_translation_field]=r[0]["l1_text"]
    except:
        n[german_translation_field]="_"
    
    i=1
    gerstring=""

    while True:
        try:
            gerstring=gerstring+ r[i]["l1_text"] +"<br>"
            i=i+1
            pass
            if i==5:
                break
        except:
            break
    n[german_translation_field_alternative]=gerstring
    
    #API 2 more information about the english word
    word_id=search_string
    url = 'https://od-api.oxforddictionaries.com/api/v2/entries/'  + uk_or_us + '/'  + word_id.lower()
    r = requests.get(url, headers = {'app_id' :ox_id , 'app_key' : ox_key})
    r=r.json()
    i=0
    english_definitions=""
    while True:
        try:
            english_definitions+=r["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][i]["definitions"][0] + "<br> <br>"
            i+=1
        except:
            break
    n[english_definitions_field]=english_definitions
    i=0
    example_sentences=""        
    examples_prepared=""        
    while True:
        try:
            example_sentences+=r["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0]["examples"][i]["text"] + "<br> <br>"
            examples_prepared+=r["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0]["examples"][i]["text"] + "<br> <br>"
            examples_prepared=examples_prepared.replace(search_string,"___")
            i+=1
        except:
            break
    n[examples_prepared_field]=examples_prepared
    n[example_sentences_entry]=example_sentences
    i=0
    etymology=""
    while True:
        try:
            etymology+=r["results"][0]["lexicalEntries"][0]["entries"][0]["etymologies"][i] + "<br>"
            i+=1
        except:
            break
    soundurl=""
    i=-1
    while True:
        try:
            i+=1
            soundurl=soundurl+r["results"][0]["lexicalEntries"][0]["entries"][0]["pronunciations"][i]["audioFile"]
            break
        except IndexError: 
            break
        except JSONDecodeError:
            break
        except KeyError as e:
            if e.args[0]=="results":
                break
            else:
                continue
        except:
            break
    try:
        url=soundurl
        print(soundurl)
        doc=requests.get(url,headers = {'app_id' :ox_id , 'app_key' : ox_key})
        with open("C:/Users/"+windowsusername + "/AppData/Roaming/Anki2/"+ ankiusername+ "/collection.media/" + search_string+"_us_1.mp3","wb") as f:
            f.write(doc.content)
    except Exception as e:
        n[pronunciation_field]=e.args[0]
    else:
        n[pronunciation_field]="[sound:" + search_string + "_us_1.mp3]"

    n[etymology_field]=etymology
    #API 3
    try:
        url = "https://twinword-language-scoring.p.rapidapi.com/word/"

        params = {"entry":search_string}

        headers = {
        'x-rapidapi-key': twinword_key,
        'x-rapidapi-host': "twinword-language-scoring.p.rapidapi.com"
        }
        r = requests.get(url, headers = headers,params=params)
        r=r.json()
        try:
            n[difficulty_score_field]=str(r["ten_degree"])
        except KeyError:
            n[difficulty_score_field]=""
    except:
        n[difficulty_score_field]=""
    #API 4 urban dictionary
    urbanendpoint="https://mashape-community-urban-dictionary.p.rapidapi.com/define"
    params={"term":search_string}
    headers={
    'x-rapidapi-host': 'mashape-community-urban-dictionary.p.rapidapi.com',
    'x-rapidapi-key': urban_key}
    r=requests.get(url=urbanendpoint,params=params,headers=headers)
    r=r.json()  
    try:
        n[slang_information_field]=r["list"][0]["definition"]
    except:
        pass
    try:
        n[slang_example_field]=r["list"][0]["example"]
    except:
        pass
    try:
        n[slang_url_field]=r["list"][0]["permalink"]
    except:
        pass


    editorWindow.editor.loadNote()
def menu_popup(self,menu):
    
    global editorWindow
    editorWindow=self
    a=menu.addAction("Fill with English information")
    a.triggered.connect(fill_the_fields)

addHook('EditorWebView.contextMenuEvent', menu_popup)