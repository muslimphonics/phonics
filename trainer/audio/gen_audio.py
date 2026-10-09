"""MuslimPhonics Reading Trainer – fabrique les voix avec ElevenLabs.
Usage (dans le dossier trainer/audio/) :
   ELEVENLABS_API_KEY=xxx python3 gen_audio.py            → tout
   DRY=1 ...                                              → montre seulement la voix, le nombre de fichiers et de caractères
   MAXCHARS=20000 ...                                     → s'arrête avant de dépasser 20 000 caractères
Ordre : niveau t d'abord, puis p, i, n… (mots, phrases en contexte, histoires).
Les fichiers déjà présents ne sont PAS refaits (on peut relancer le mois suivant sans payer deux fois).
Les 42 sons (snd/1.mp3 … snd/42.mp3) sont enregistrés par Alice, pas ici."""
import os,sys,json,time,urllib.request,urllib.parse
KEY=os.environ.get('ELEVENLABS_API_KEY') or sys.exit('Il manque ELEVENLABS_API_KEY')
MODEL=os.environ.get('MODEL','eleven_multilingual_v2')
SPEED=float(os.environ.get('SPEED','0.9'))
MAXC=int(os.environ.get('MAXCHARS','0'))
H={'xi-api-key':KEY,'Content-Type':'application/json'}
def api(url,data=None):
    r=urllib.request.Request(url,data=json.dumps(data).encode() if data else None,headers=H,method='POST' if data else 'GET')
    return urllib.request.urlopen(r,timeout=60).read()
try:
    sub=json.loads(api('https://api.elevenlabs.io/v1/user/subscription'))
    print('Crédits restants ce mois :',sub['character_limit']-sub['character_count'],'caractères')
except Exception as e: print('(crédits restants non lisibles avec cette clé)')
VID=os.environ.get('VOICE_ID')
if not VID:
    NAME=os.environ.get('VOICE_NAME','Beth')   # voix de Reading Book 1
    vs=json.loads(api('https://api.elevenlabs.io/v2/voices?page_size=100&search='+urllib.parse.quote(NAME)))['voices']
    vs=[v for v in vs if v['name'].lower().startswith(NAME.lower())] or vs
    if not vs: sys.exit(f"Voix '{NAME}' introuvable : donne VOICE_ID=... (ElevenLabs > Voices > ... > Copy voice ID)")
    if len(vs)>1: print('Plusieurs voix trouvées :',[v['name'] for v in vs],'→ je prends la première')
    VID=vs[0]['voice_id']; print('Voix :',vs[0]['name'],VID)
jobs=[l.rstrip('\n').split('\t') for l in open('jobs.tsv',encoding='utf-8') if l.strip()]
todo=[j for j in jobs if not os.path.exists(j[0])]
if MAXC:
    keep=[];c=0
    for j in todo:
        if c+len(j[1])>MAXC: break
        keep.append(j); c+=len(j[1])
    todo=keep
print(f"{len(todo)} fichiers à créer ({sum(len(j[1]) for j in todo)} caractères), du niveau {todo[0][2] if todo else '-'} au niveau {todo[-1][2] if todo else '-'}")
if os.environ.get('DRY') or not todo: sys.exit()
for d in ('w','s','p'): os.makedirs(d,exist_ok=True)
for n,(f,t,lv) in enumerate(todo,1):
    for essai in range(4):
        try:
            mp3=api(f'https://api.elevenlabs.io/v1/text-to-speech/{VID}?output_format=mp3_44100_64',
                    {'text':t,'model_id':MODEL,'voice_settings':{'stability':0.5,'similarity_boost':0.75,'speed':SPEED}})
            open(f,'wb').write(mp3); break
        except Exception as e:
            print('  erreur',f,e); time.sleep(5*(essai+1))
            if '401' in str(e) or 'quota' in str(e).lower(): sys.exit('Clé refusée ou crédits épuisés : arrêt.')
    if n%50==0: print(n,'/',len(todo))
print('Terminé.')
