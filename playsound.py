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



from threading import Thread,Event



class music(object):
    
    __alias=None
    __running_idx=None
    __sound=None
    __start=None
    __end=None
    __is_repeat=False
    __time=None

    '''
        initialize the music object
    '''
    def __init__(self,sound):
        self.__alias=['','']
        self.__running_idx=0
        self.__time=0
        self.preload(sound)


    

    
    '''
        seek the music to pos.
        music will bee paused
    '''
    def seek(self,pos):
        if self.__check_alias():
            if pos>self.__end or pos<self.__start:
                raise PlaysoundException('position exceed range')
            self.pause()
            self.__time=self.__end-pos
            winCommand('seek',self.__get_alias(),'to',str(pos))

    '''
        clear the music object
        music will be closed
    '''
    def close(self):
        self.stop()
        self.__clear()


    '''
        set  repeat flag of the music
        music will repeatly play
    '''
    def set_repeat(self,repeat):
        self.__is_repeat=repeat


    '''
        return the range from start to end
        music will not be effected
    '''
    def length(self):
        if self.__check_alias():
            return self.__end-self.__start

    '''
        return the mode of the music object
        music will not be effected
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
            self.__time=self.__end-self.position()
                
    '''
        play the music from start to end
        music will be playing
    '''
    def play(self,start=0,end=-1):
        self.__start,self.__end=self.__parse_start_end(start,end,self.total_length())
        self.__play_implement(start,end)
    

    '''
        return the position of the music
        music will not be effected
    '''
    def position(self):
        if self.__check_alias():
            return int(winCommand('status',self.__get_alias(),'position').decode())
        else:
            return 0

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
        self.__time=0
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
                winCommand('resume '+self.__alias)


    '''
        stop the music.
        music will be stopped
    '''
    def stop(self):
        if self.__check_alias():
            self.seek(self.__start)
            winCommand('stop '+self.__get_alias())
            self.__time=0

            
    '''
        total_length of the music object, the difference that total_length is the range is total music,
        but length is only range from start to end
        music will not be effected
    '''
    def total_length(self):
        if self.__check_alias():
            return int(winCommand('status',self.__get_alias(),'length').decode())
    

    '''
        update the record time of the music, 
    '''
    #     if the music is playing, then the remaining time should be subtract from time.
    #     However sometimes the music is stopped,but the record time is not as same as the real remaining time of the music.
    #     Thus you should also consider the situation when music is stopped.
    def update_time(self,time):
        mod = self.mode()
        if mod=='paused':
            return 0
        if mod=='playing' or mod =='stopped':
            self.__time=self.__time-time
            
            if self.__time<=0:
                #if time <0, then repeat the music or stop the music
                if self.__is_repeat==True:
                    self.__running_idx=(self.__running_idx+1)%2
                    self.__time=self.length()
                    self.__play_implement(self.__start,self.__end)
                    return 0
                else:
                    self.__time=0
                    return 1
        print('pos  rt  mode')
        print(self.position(),self.__time,mod)
    
        
    
    def __get_alias(self):
        return self.__alias[self.__running_idx]
    
    
    def __check_alias(self):
        return self.__get_alias()!=''

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
            return self.__sound

    def __play_implement(self,start,end):
        self.__time=end - start
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


# class music_player(object):
    
#     __alias=None
#     __running_idx=None
#     __sound=None
    
#     __end=None
#     __end_loop_event=None
#     __loop_event=None
#     __is_repeat=False
#     __is_block=False
#     __pos=None
#     __mod=None
#     def __init__(self,sound=None):
#         self.__alias=['','']
#         self.__running_idx=0
#         self.__loop_event=Event()
#         self.__end_loop_event=Event()
#         self.preload(sound)
#         self.__loop_event.set()
#         self.__end_loop_event.set()

    

#     '''preload the music information'''
#     def preload(self,sound):
#         if sound=='' or sound==None:
#             self.__start=0
#             self.__end = self.total_length()
#             return 0
#         self.__sound=sound
#         for i in range(2):
#             self.__alias[i]='playsound_'+str(random())
#             winCommand('open "'+self.__sound+'" alias',self.__alias[i])
#             winCommand('set',self.__alias[i],'time format milliseconds')
        
        
#         length=self.total_length()
#         self.__start=0
#         self.__end=length
#         return length

#     # def seek(self,pos):
#     #     if self.__check_alias():
#     #         if pos>self.__end or pos<self.__start:
#     #             raise PlaysoundException('position exceed range')
#     #         self.stop()
#     #         if self.__is_repeat:
#     #             self.__pos = pos
#     #             self.__is_repeat=False
#     #         else:
#     #             winCommand('seek',self.__alias,'to',str(self.position()))

#     def free(self):
#         self.stop()
#         self.__clear()

#     def length(self):
#         if self.__check_alias():
#             return self.__end-self.__start

#     def mode(self):
#         if self.__check_alias():
#             return winCommand('status',self.__get_alias(),'mode').decode()

#     def pause(self):
#         if self.__check_alias():
#             if self.__is_repeat:
#                 self.stop()
#             else:
#                 winCommand('pause '+self.__alias)

#     def play(self,sound=None,block=False,repeat=False,start=0,end=-1):
#         self.stop()

#         if sound==None:         #play last sound
#             sound = self.__sound
#         elif self.__sound!=sound: #play new  sound
#             self.__clear()
#         else:                   #play same sound
#             pass                


#         self.preload(sound)
#         self.__play_implement(start,end,repeat,block,self.position())


#     def play_from(self,start,end=-1,block=False,repeat=False):
#         if self.__check_alias():
#             # self.stop()
#             #TODO :some thing wrong
#             # self.position()
#             self.__play_implement(start,end,repeat,block,0)
    

#     def position(self):
#         if self.__check_alias():
#                 return int(winCommand('status',self.__get_alias(),'position').decode())

#     def resume(self):
#         if self.__check_alias():
#             if self.__is_repeat:
#                 self.__play_implement(self.__start,self.__end,self.__is_repeat,self.__is_block,self.position())
#             else:
#                 winCommand('resume '+self.__alias)

#     def stop(self):
#         if self.__check_alias():
#             self.__loop_event.set()
#             self.__end_loop_event.wait()

#             winCommand('stop '+self.__get_alias())
            
#             # sleep(1)
#             # self.__mod='stopped'
    
#     def total_length(self):
#         if self.__check_alias():
#             print(self.__get_alias())
#             return int(winCommand('status',self.__get_alias(),'length').decode())
    
        
    
#     def __get_alias(self):
#         return self.__alias[self.__running_idx]
    
    
#     def __check_alias(self):
#         return self.__get_alias()!=''

#     def __parse_start_end(self,start,end,length):
#         if not (isinstance(start,int) and isinstance(end,int)):
#             raise PlaysoundException('start and end must be int')
#         _start=0
#         _end=0
#         if end==-1:
#             _end = length
#         elif end<=length:
#             _end = end
#         else:
#             raise PlaysoundException('music range exceed limits')
#         if start<0 or start>length:
#             raise PlaysoundException('music range exceed limits')
#         elif _end<start:
#             raise PlaysoundException('end must be bigger than start')
#         else:
#             _start=start
#         return _start,_end

#     def __del__(self):
#         self.__clear()
    
#     def __clear(self):
#         if self.__check_alias():
#             for i in range(2):
#                 winCommand('close '+self.__alias[i])
#             self.__alias=['','']
#             self.__end=None
#             self.__loop_event.set()
#             self.__end_loop_event.set()
#             self.__is_repeat=False
#             self.__is_block=False
#             # print('remain sound:',self.__sound)
#             return self.__sound
#         else:
#             return self.__sound

#     def __play_implement(self,start,end,repeat,block,pos):
#         self.__start,self.__end=self.__parse_start_end(start,end,self.total_length())
#         self.__is_repeat=repeat
#         self.__is_block=block
#         if repeat:
#             #clear repeat event
#             self.__loop_event.clear()
#             self.__end_loop_event.clear()
#             print(self.total_length())
#             t=Thread(target=self.__loop_music,args=(self,self.__sound,self.__start,self.__end,int(pos)))
#             t.start()
#             t.join()
            
#         else:
#             winCommand('play',self.__get_alias(),'from '+ str(self.__start) +' to',str(self.__end))
#             if block:
#                 sleep(self.length()/1000)

    
#     '''
#         gapless music loop
#     '''
#     @staticmethod
#     def __loop_music(master,sound,start,end,pos):
#         master.__end_loop_event.set()
#         master.free()
#         master.preload(sound)
#         def loop_and_check(master,start,stop,step):
#             for x in range(start,stop,step):
#                 if master.__loop_event.isSet():
#                     master.__end_loop_event.set()
#                     # master.stop()
#                     return 1
#                 sleep(step/1000)
#             return 0
#         if not isinstance(master,music_player) or master.__loop_event==None:
#             raise PlaysoundException('master must be a music player')
#         cnt=0
#         delay=100
#         stop = max(end-delay,delay)
        
#         step = min(delay,end-start)
#         if pos>=end :
#             raise PlaysoundException('pos must be smaller than end')

#         #loop from pause position
#         master.play_from(start=pos,end=end)
#         if loop_and_check(master,pos,stop,step):
#             return
#         cnt=(cnt+1)%2
        
#         #loop music
#         while True:
#             winCommand('play',master.__alias[master.__running_idx],'from '+ start +' to',end)
#             # lm[cnt].play_from(start=start,end=end)
#             if loop_and_check(master,start,stop,step):
#                 return
#             master.__running_idx=(master.__running_idx+1)%2
    

#     def print(self):
#         if self.__check_alias():
#             def format_miliseconds(t):
#                 return '%d:%d:%d.%d'%(t//3600000,(t%3600000)//60000,(t%60000)//1000,t%1000)

#             print('music name:',self.__sound)
#             print('mode：',self.mode())
#             print('total_length：',self.total_length())
#             print('position:',str(self.position()))
#             print('start - end: {} - {}'.format(format_miliseconds(self.__start),format_miliseconds(self.__end)))