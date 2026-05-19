#!/bin/python3
import datetime,json,os,sqlite3,urllib.request
os.makedirs(os.path.expanduser('~/animethemes-audios'),exist_ok=1)
os.chdir(os.path.expanduser('~/animethemes-audios'))
for n in*os.listdir(),'18921028'+12*'0':
    try:
        less_date=datetime.datetime.strptime(n,'%Y%m%d%H%M%S%f').strftime('%Y-%m-%dT%H:%M:%S.%f')
        db=n
        break
    except:0
with urllib.request.urlopen(urllib.request.Request(
    f'https://api.animethemes.moe/audio?fields[audio]=id,link,path,updated_at&filter[updated_at-gt]={less_date}&page[size]=1&sort=updated_at'
    ,headers={'User-Agent':'curl'}))as r:audio,=json.load(r)['audios']
with urllib.request.urlopen(audio['link'])as r:moe=r.read()
with sqlite3.connect(db)as c:
    c.execute('CREATE TABLE IF NOT EXISTS audios(id UNIQUE,path)')
    p,=next(c.execute('SELECT path FROM audios WHERE id=:id',audio),[0])
    if p:
        os.unlink(p)
        while 1:
            try:os.rmdir(p:=os.path.dirname(p))
            except:break
        c.execute('DELETE FROM audios WHERE id=:id',audio)
os.makedirs(os.path.dirname(audio['path']),exist_ok=1)
with open(audio['path'],'bw')as f:f.write(moe)
with sqlite3.connect(db)as c:c.execute('INSERT INTO audios VALUES(:id,:path)',audio)
more_date=datetime.datetime.fromisoformat(audio['updated_at'])
os.replace(db,more_date.strftime('%Y%m%d%H%M%S%f'))
if(datetime.datetime.now(datetime.UTC)-more_date).days>7:
    if'dai'in __file__:os.rename(__file__,__file__.replace('dai','hour'))
else:
    if'hour'in __file__:os.rename(__file__,__file__.replace('hour','dai'))
