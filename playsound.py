class PlaysoundException(Exception):
    pass

def _playsoundWin(sound, block = True):
    '''
    Utilizes windll.winmm. Tested and known to work with MP3 and WAVE on
    Windows 7 with Python 2.7. Probably works with more file formats.
    Probably works on Windows XP thru Windows 10. Probably works with all
    versions of Python.

    Inspired by (but not copied from) Michael Gundlach <gundlach@gmail.com>'s mp3play:
    https://github.com/michaelgundlach/mp3play

    I never would have tried using windll.winmm without seeing his code.
    '''
    from ctypes import c_buffer, windll
    from random import random
    from time   import sleep
    from sys    import getfilesystemencoding
    def winCommand(*command):
        buf = c_buffer(255)
        command = ' '.join(command).encode(getfilesystemencoding())
        errorCode = int(windll.winmm.mciSendStringA(command, buf, 254, 0))
        if errorCode:
            errorBuffer = c_buffer(255)
            windll.winmm.mciGetErrorStringA(errorCode, errorBuffer, 254)
            exceptionMessage = ('\n    Error ' + str(errorCode) + ' for command:'
                                '\n        ' + command.decode() +
                                '\n    ' + errorBuffer.value.decode())
            raise PlaysoundException(exceptionMessage)
        return buf.value

    alias = 'playsound_' + str(random())
    winCommand('open "' + sound + '" alias', alias)
    winCommand('set', alias, 'time format milliseconds')
    durationInMS = winCommand('status', alias, 'length')
    winCommand('play', alias, 'from 0 to', durationInMS.decode())

    if block:
        sleep(float(durationInMS) / 1000.0)

def _playsoundOSX(sound, block = True):
    '''
    Utilizes AppKit.NSSound. Tested and known to work with MP3 and WAVE on
    OS X 10.11 with Python 2.7. Probably works with anything QuickTime supports.
    Probably works on OS X 10.5 and newer. Probably works with all versions of
    Python.

    Inspired by (but not copied from) Aaron's Stack Overflow answer here:
    http://stackoverflow.com/a/34568298/901641

    I never would have tried using AppKit.NSSound without seeing his code.
    '''
    from AppKit     import NSSound
    from Foundation import NSURL
    from time       import sleep

    if '://' not in sound:
        if not sound.startswith('/'):
            from os import getcwd
            sound = getcwd() + '/' + sound
        sound = 'file://' + sound
    url   = NSURL.URLWithString_(sound)
    nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
    if not nssound:
        raise IOError('Unable to load sound named: ' + sound)
    nssound.play()

    if block:
        sleep(nssound.duration())

def _playsoundNix(sound, block=True):
    """Play a sound using GStreamer.

    Inspired by this:
    https://gstreamer.freedesktop.org/documentation/tutorials/playback/playbin-usage.html
    """
    if not block:
        raise NotImplementedError(
            "block=False cannot be used on this platform yet")

    # pathname2url escapes non-URL-safe characters
    import os
    try:
        from urllib.request import pathname2url
    except ImportError:
        # python 2
        from urllib import pathname2url

    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst

    Gst.init(None)

    playbin = Gst.ElementFactory.make('playbin', 'playbin')
    if sound.startswith(('http://', 'https://')):
        playbin.props.uri = sound
    else:
        playbin.props.uri = 'file://' + pathname2url(os.path.abspath(sound))

    set_result = playbin.set_state(Gst.State.PLAYING)
    if set_result != Gst.StateChangeReturn.ASYNC:
        raise PlaysoundException(
            "playbin.set_state returned " + repr(set_result))

    # FIXME: use some other bus method than poll() with block=False
    # https://lazka.github.io/pgi-docs/#Gst-1.0/classes/Bus.html
    bus = playbin.get_bus()
    bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
    playbin.set_state(Gst.State.NULL)


from platform import system
system = system()

if system == 'Windows':
    playsound = _playsoundWin
elif system == 'Darwin':
    playsound = _playsoundOSX
else:
    playsound = _playsoundNix

del system


from ctypes import c_buffer, windll
from random import random
from time   import sleep
from sys    import getfilesystemencoding
def winCommand(*command):
    buf = c_buffer(255)
    command = ' '.join(command).encode(getfilesystemencoding())
    errorCode = int(windll.winmm.mciSendStringA(command, buf, 254, 0))
    if errorCode:
        errorBuffer = c_buffer(255)
        windll.winmm.mciGetErrorStringA(errorCode, errorBuffer, 254)
        exceptionMessage = ('\n    Error ' + str(errorCode) + ' for command:'
                            '\n        ' + command.decode() +
                            '\n    ' + errorBuffer.value.decode())
        raise PlaysoundException(exceptionMessage)
    return buf.value



from threading import Thread,Event,Lock
from queue import Queue,Empty
from collections import deque

'''
    music class which uses windows mci to play the music
'''
class _music(object):
    
    __alias=None
    __running_idx=None
    __sound=None
    __start=None
    __end=None
    __is_repeat=False
    __id=-1
    music_list=None
    '''
        initialize the music object
    '''
    def __init__(self,sound,id):
        self.__alias=['','']
        self.__running_idx=0
        self.__id=id
        self.preload(sound)
        
    def set_music_list(self,music_list):
        self.music_list = music_list
    
    def __eq__(self,value):
        return self.__id==value
    

    '''
        clear the music object
        music will be closed
    '''
    def close(self):
        self.stop()
        self.__clear()

    '''
        get id of music
        music will not be affected
    '''
    def get_id(self):
        return self.__id

    '''
        return whether music plays repeatly
        music will not be affected
    '''
    def is_repeat(self):
        return self.__is_repeat


    '''
        return the range from start to end
        music will not be affected
    '''
    def length(self):
        if self.__check_alias():
            return self.__end-self.__start

    '''
        return the mode of the music object
        music will not be affected
    '''
    def mode(self):
        if self.__check_alias():
            return winCommand('status',self.__get_alias(),'mode').decode()

    '''
        pause the music
        music will be paused
    '''
    def pause(self):
        if self.__check_alias():
            winCommand('pause '+self.__get_alias())
                
    '''
        play the music from start to end
        music will be playing
    '''
    def play(self,start=0,end=-1):
        
        self.__start,self.__end=self.__parse_start_end(start,end,self.total_length())
        self.__play_implement(self.__start,self.__end)
    

    '''
        return the position of the music
        music will not be affected
    '''
    def position(self):
        if self.__check_alias():
            return int(winCommand('status',self.__get_alias(),'position').decode())

    '''
        preload the music information
    '''
    def preload(self,sound):
        self.__sound=sound
        for i in range(2):
            self.__alias[i]='playsound_'+str(random())
            winCommand('open "'+self.__sound+'" alias',self.__alias[i])
            winCommand('set',self.__alias[i],'time format milliseconds')
        
        
        length=self.total_length()
        self.__start=0
        self.__end=length
        return length

    
    '''
        resume playing
        music will be playing
    '''
    def resume(self):
        if self.__check_alias():
            if self.__is_repeat:
                self.__play_implement(self.position(),self.__end)
            else:
                winCommand('resume '+self.__get_alias())
    
    '''
        seek the music to pos.
        music will bee paused
    '''
    def seek(self,pos):
        if self.__check_alias():
            if pos>self.__end or pos<self.__start:
                raise PlaysoundException('position exceed range')
            
            winCommand('seek',self.__get_alias(),'to',str(pos))
            winCommand('play',self.__get_alias(),'from '+ str(pos) +' to',str(self.__end))
            self.pause()
            

    '''
        set  repeat flag of the music
        music will repeatly play
    '''
    def set_repeat(self,repeat):
        self.__is_repeat=repeat


    '''
        set id for music object
        music will not be affected
    '''
    def set_id(self,id):
        self.__id=id

    '''
        stop the music.
        music will be stopped
    '''
    def stop(self):
        if self.__check_alias():
            self.seek(self.__start)
            winCommand('stop '+self.__get_alias())

            
    '''
        total_length of the music object, the difference that total_length is the range is total music,
        but length is only range from start to end
        music will not be affected
    '''
    def total_length(self):
        if self.__check_alias():
            return int(winCommand('status',self.__get_alias(),'length').decode())
    

    '''
        update the record time of the music, 
    '''
    def update_mode(self,delay=0):
        mod = self.mode()

        if mod =='playing':
                #if self.__end-self.position()<delay then repeat the music
                if self.__is_repeat==True:
                    if self.__end-self.position()<=delay:
                        self.__running_idx=(self.__running_idx+1)%2
                        self.__play_implement(self.__start,self.__end)
        return mod
       
        
    
        
    
    def __get_alias(self):
        return self.__alias[self.__running_idx]
    
    
    def __check_alias(self):
        if self.__get_alias()!='':
            return True

    def __parse_start_end(self,start,end,length):
        if not (isinstance(start,int) and isinstance(end,int)):
            raise PlaysoundException('start and end must be int')
        _start=0
        _end=0
        if end==-1:
            _end = length
        elif end<=length:
            _end = end
        else:
            raise PlaysoundException('music range exceed limits')
        if start<0 or start>length:
            raise PlaysoundException('music range exceed limits')
        elif _end<start:
            raise PlaysoundException('end must be bigger than start')
        else:
            _start=start
        return _start,_end

    def __del__(self):
        self.__clear()
    
    def __clear(self):
        if self.__check_alias():
            for i in range(2):
                winCommand('close '+self.__alias[i])
            self.__alias=['','']
            self.__start=None
            self.__end=None
            self.__is_repeat=False

    def __play_implement(self,start,end):
        winCommand('play',self.__get_alias(),'from '+ str(start) +' to',str(end))
    

    def print(self):
        if self.__check_alias():
            def format_miliseconds(t):
                return '%d:%d:%d.%d'%(t//3600000,(t%3600000)//60000,(t%60000)//1000,t%1000)

            print('music name:',self.__sound)
            print('mode：',self.mode())
            print('total_length：',self.total_length())
            print('position:',str(self.position()))
            print('start - end: {} - {}'.format(format_miliseconds(self.__start),format_miliseconds(self.__end)))

'''
    singleton
'''
class _singleton(object):
    _mutex=Lock()
    def __init__(self):
        pass

    
    @classmethod
    def GetInstance(cls,*args,**kwargs):
        if not hasattr(cls,'_instance'):
            cls._mutex.acquire()  
            if not hasattr(cls,'_instance'):
                cls._instance = cls()
                print('create instance',cls._instance)
            cls._mutex.release()
        return cls._instance

'''
    music tag is used to send message for music manager
'''
class _music_tag(object):
    id=-1               #id is the connection between music player and _music object
    operator=''         #operator of _music object
    args=None           #parameters
    block_event=None    
    block=False
    retval=None         #return value for some methods of music player
    music_list=None     #special deal with music list
    def __init__(self,id,operator,block=False,*args):
        self.id=id
        self.operator = operator
        self.args = args
        if block:
            self.block_event=Event()
            self.block=True

    def set_music_list(self,music_list):
        self.music_list = music_list

'''
    music player is the client who sends music tags to music manager which indeed plays music.
    music player controls music once you open the music.
'''
class music_player(object):
    __id=-1         #identity of every _music object
    __music=None    #sound
    static_id=0     #static variables
    mutex=Lock()    #lock of static_id
    music_list=None #this music player belong to which music list 

    
    def __init__(self,music_list=None):
        '''
            if music player belongs to one of music list,then set music_list,
            otherwise you can ignore music_list parameter
        '''
        self.music_list = music_list

    
    def get_music(self):
        '''
            get name of sound
        '''
        return self.__music


    def close(self):
        '''
            close sound
        '''
        self.__send('close',False)
        self.__id=-1

    
    def length(self):
        '''
            get the length of music.

            @warning: this method blocks current thread until music manager respond this functions
        '''
        return self.__send('length',True)

    
    def mode(self):
        '''
            get the mode of music.

            @warning: this method blocks current thread until music manager respond this functions
        '''
        return self.__send('mode',True)

    
    def open(self,music):
        '''
            open the music
        '''
        self.__music=music

        self.mutex.acquire()
        self.__id=music_player.static_id
        music_player.static_id=music_player.static_id+1
        self.mutex.release()

        self.__send('open',False,self.__music,self.__id)

    
    def pause(self):
        '''
            pause the music
        '''
        self.__send('pause',False)

    
    def play(self,start=0,end=-1):
        '''
            play the music
        '''
        self.__send('play',False,start,end)


    
    def position(self):
        '''
            get the mode of music.

            @warning: this method blocks current thread until music manager respond this functions
        '''
        return self.__send('position',True)

    def resume(self):
        '''
            resume the music
        '''
        self.__send('resume',False)

    
    def seek(self,pos):
        '''
            seek the music to pos, which is defined in miliseconds
        '''
        self.__send('seek',False,pos)

    
    def set_repeat(self,repeat):
        '''
            play music repeatly
        '''
        self.__send('set_repeat',False,repeat)

    
    def stop(self):
        '''
            stop the music
        '''
        self.__send('stop',False)


    
    def total_length(self):
        '''
            get the total length of music.
            
            @warning: this method blocks current thread until music manager respond this functions
        '''
        return self.__send('total_length',True)

    
    def __send(self,operator,block,*args):
        '''
            send music tag to music manager
        '''
        if self.__id==-1:
            raise PlaysoundException('No music has been opened')
        tag=_music_tag(self.__id,operator,block,*args)
        tag.music_list=self.music_list
        return music_manager.GetInstance().put_tag(tag)


class music_list(object):
    __music_list=deque()
    def append_music(self,sound,repeat=False):
        music = music_player(self)
        
        music.open(sound)
        music.set_repeat(repeat)
        self.__music_list.append(music)
        if len(self.__music_list)==1:
            self.top().play()

    def play_next(self):
        if len(self.__music_list)>=2:
            self.__music_list[1].play()
            self.__music_list.popleft().close()
            

    
    def pause_music(self):
        if len(self.__music_list)>0 and self.mode()=='playing':
            self.top().pause()
        
    def resume_music(self):
        if len(self.__music_list)>0 and self.mode()=='paused':
            self.top().resume()

    def mode(self):
        return self.top().mode()
    
    def top(self):
        return self.__music_list[0]


class music_manager(_singleton):
    __mutex=Lock()
    __sounds=[]
    # __music_list=[]
    __tag_queue=Queue()
    __running_event=Event()
    __end_running_event=Event()

    def __init__(self):
        self.reset_event()

    def reset_event(self):
        self.__running_event.set()
        self.__end_running_event.clear()

    def put_tag(self,tag):
        '''
            push a music tag to music_manager

            @warning: if tag.block is True ,this method will block current thread until music manager respond this functions
        '''
        if tag.block:
            tag.block_event.clear()
        self.__tag_queue.put(tag)
        if tag.block:
            tag.block_event.wait()
            
        return tag.retval

    def get_tag(self):
        try:
            #if there is no task for music player, then sleep the music manager,
            #otherwise get a tag immediately
            if len(self.__sounds)>0:
                tag=self.__tag_queue.get_nowait()
            else:
                tag=self.__tag_queue.get()
            retval=None
            if tag.operator == 'open':
                m=self.__add_music(*tag.args)
                m.set_music_list(tag.music_list)
            elif tag.operator == 'close':
                #remove the music from self.__sounds
                self.__rm_music(tag.id)
            else:
                (idx,item)=self.__get_music_idx_and_item(tag.id)
                #reflect
                retval=getattr(item,tag.operator)(*tag.args)
            
            #set return values in tag
            if tag.block==True:
                tag.retval=retval
                tag.block_event.set()
        except Empty:
            pass
    
    def __add_music(self,sound,id): 
        m=_music(sound,id)
        self.__mutex.acquire()
        self.__sounds.append(m)
        self.__mutex.release()

        return m

    def __rm_music(self,id):
        idx,rm_item=self.__get_music_idx_and_item(id)
        rm_item.close()
        rm_item.set_id(-1)
        self.__mutex.acquire()
        self.__sounds.pop(idx)
        self.__mutex.release()

    def __get_music_idx_and_item(self,id):
        for i,x in enumerate(self.__sounds):
            if x.get_id()==id:
                return i,x
        raise PlaysoundException('Unknown music object found')

    

            

    @classmethod
    def start(cls):
        '''
            start the music manager
        '''
        Thread(target=music_manager._start_music_manager_impl).start()

    

    @classmethod
    def stop(cls):
        '''
            stop the music manager
        '''
        manager = cls.GetInstance()
        manager.__running_event.clear()
        manager.__end_running_event.wait()
        manager.reset_event()
        print('stop manager',manager)


    '''
        main loop of music manager
    '''
    @classmethod
    def _start_music_manager_impl(cls):
        manager = cls.GetInstance()
        print('start manager',manager)
        delay=100
        
        
        while(manager.__running_event.isSet()):
            for m in manager.__sounds:
                mode = m.update_mode(delay)

                #callback the music_list
                if m.music_list!=None and mode=='playing' and not m.is_repeat():
                    pos = m.position()
                    total_length=m.total_length()
                    if  total_length-pos<=delay:
                        m.music_list.play_next()            

            manager.get_tag()
            
            
        for x in manager.__sounds:
            x.close()
        
        manager.__end_running_event.set()


music_manager.start()