"""MuslimPhonics Reading Trainer – fabrique les voix avec ElevenLabs.
Usage (dans le dossier trainer/audio/) :  ELEVENLABS_API_KEY=xxx python3 gen_audio.py
Crée w/<mot>.mp3 (un fichier par mot) s/<niveau>-<ligne>.mp3 (une phrase d'histoire) et p/<mot>.mp3 (phrase en contexte).
Les 42 sons (snd/1.mp3 … snd/42.mp3) sont enregistrés par Alice, pas ici.
Les fichiers déjà présents ne sont PAS refaits (on peut relancer sans payer deux fois)."""
import os,sys,json,time,urllib.request,urllib.parse
KEY=os.environ.get('ELEVENLABS_API_KEY') or sys.exit('Il manque ELEVENLABS_API_KEY')
MODEL=os.environ.get('MODEL','eleven_multilingual_v2')  # plus fiable que v3 pour des mots isolés
SPEED=float(os.environ.get('SPEED','0.9'))
H={'xi-api-key':KEY,'Content-Type':'application/json'}
def api(url,data=None):
    r=urllib.request.Request(url,data=json.dumps(data).encode() if data else None,headers=H,method='POST' if data else 'GET')
    return urllib.request.urlopen(r,timeout=60).read()
VID=os.environ.get('VOICE_ID')
if not VID:
    vs=json.loads(api('https://api.elevenlabs.io/v2/voices?page_size=100&search='+urllib.parse.quote('Daniel')))['voices']
    vs=[v for v in vs if 'warm' in v['name'].lower()] or vs
    if not vs: sys.exit("Voix 'Daniel' introuvable : donne VOICE_ID=... (ElevenLabs > Voices > ... > Copy voice ID)")
    VID=vs[0]['voice_id']; print('Voix :',vs[0]['name'],VID)
jobs=[('w/'+w.lower().replace("'",'')+'.mp3', 'I.' if w=='I' else w+'.') for w in open('words.txt').read().split()]
jobs+=[('s/'+k+'.mp3',txt) for k,txt in (l.rstrip('\n').split('\t',1) for l in open('stories.tsv',encoding='utf-8') if l.strip())]
jobs+=[('p/'+k+'.mp3',txt) for k,txt in (l.rstrip('\n').split('\t',1) for l in open('sentences.tsv',encoding='utf-8') if l.strip())]
todo=[(f,t) for f,t in jobs if not os.path.exists(f)]
print(f'{len(todo)} fichiers à créer sur {len(jobs)} ({sum(len(t) for f,t in todo)} caractères ElevenLabs)')
if os.environ.get('DRY'): sys.exit()
os.makedirs('w',exist_ok=True); os.makedirs('s',exist_ok=True); os.makedirs('p',exist_ok=True)
for n,(f,t) in enumerate(todo,1):
    for essai in range(4):
        try:
            mp3=api(f'https://api.elevenlabs.io/v1/text-to-speech/{VID}?output_format=mp3_44100_64',
                    {'text':t,'model_id':MODEL,'voice_settings':{'stability':0.5,'similarity_boost':0.75,'speed':SPEED}})
            open(f,'wb').write(mp3); break
        except Exception as e:
            print('  erreur',f,e); time.sleep(5*(essai+1))
    if n%50==0: print(n,'/',len(todo))
print('Terminé.')
