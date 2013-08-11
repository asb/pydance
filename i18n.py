import gettext
import locale
import os.path,sys

def MyDir():
    filename = sys.argv[0]
    return os.path.abspath(os.path.dirname(filename))

mydir=MyDir()

directories=['/usr/share/locale','/usr/local/share/locale',mydir+'/../../locale',mydir+'/../share/locale',mydir+'/mo']

lang = None
for dir in directories:
    try:
        lang=gettext.translation('pydance',dir)
        break
    except:
        pass


if lang!=None:
    lang.install(True)

else:
    gettext.install('pydance')
