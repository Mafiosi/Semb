import speech_recognition as sr
import queue
import threading
import RPi.GPIO as GPIO
import time
import vlc
import ctypes
import _thread

###########################
#####   CONFIG PINS   #####
###########################

########    OUT PINS     ########
pin_outs = [8, 10, 12, 16, 18, 22]

###    MOTOR
choco_bar_motor = 8
coke_motor = 10
gum_motor = 12                                                                                                                                                                                                                                                                                                                                                      

###    LEDS
voice_led = 16
money_ok_led = 18
money_bad_led =22

########    IN PINS PINS     ########
pin_ins = [24, 26]

### CHANGE BUTTONS
small_change = 24
big_change = 26

###########################
####  CODE SENTENCES   ####
###########################

hello = ['hello', 'alo']
chocobar = ['chocobar', 'Google', 'bar', 'chocolate', 'cocoa', 'hookah']
coke = ['Coca-Cola', 'Coke', 'Cocaine', 'cocaine','coke']
gum = ['gum','game', 'Gum','come','Come']
cash = ['money','have','change','cash']

###########################
####  SCHED CLASSES    ####
###########################

class Operation(threading.Timer):
    def __init__(self, *args, **kwargs):
        threading.Timer.__init__(self, *args, **kwargs)
        self.setDaemon(True)

    def run(self):
        while True:
            self.finished.clear()
            self.finished.wait(self.interval)
            if not self.finished.isSet():
                self.function(*self.args, **self.kwargs)
            else:
                return
            self.finished.set()

class Manager(object):

    ops = []

    def add_operation(self, operation, interval, args=[], kwargs={}):
        op = Operation(interval, operation, args, kwargs)
        self.ops.append(op)
        _thread.start_new_thread(op.run, ())

    def stop(self):
        for op in self.ops:
            op.cancel()
        self._event.set()

##################################
######    MUSIC FUNCTIONS   ######
##################################

def background_music(sound_queue,speech_lock,led_lock,f):
    global money
    #Set Volume Parameters
    volume_good = 60

    tid = ctypes.CDLL('libc.so.6').syscall(224)
    print('music', tid)
    f.write("Main Id:" + str(tid))

    #Establish Background Music
    background = vlc.MediaPlayer("background_2.mp3")
    print (background.get_instance())
    background.play()
    background.audio_set_volume(volume_good)

    #Eventually change Sounds
    while True:
        info = sound_queue.get()
        speech_lock.acquire(True)
        #CASE 1 2 3 MONEY GOOD PRODUCT COMING OUT
        if info == 1:
            background.pause()
            temp = vlc.MediaPlayer("Choco.mp3")
            temp.play()
            temp.audio_set_volume(100)
            time.sleep(3)
            temp.stop()
            background.pause()
            led_lock.acquire(True)
            GPIO.output(money_ok_led, GPIO.LOW)
            led_lock.release()
        elif info == 2:
            background.pause()
            temp = vlc.MediaPlayer("Coke.mp3")
            temp.play()
            temp.audio_set_volume(100)
            time.sleep(3)
            temp.stop()
            background.pause()
            led_lock.acquire(True)
            GPIO.output(money_ok_led, GPIO.LOW)
            led_lock.release()
        elif info == 3:
            background.pause()
            temp = vlc.MediaPlayer("Gum.mp3")
            temp.play()
            temp.audio_set_volume(100)
            time.sleep(3)
            temp.stop()
            background.pause()
            led_lock.acquire(True)
            GPIO.output(money_ok_led, GPIO.LOW)
            led_lock.release()

        #CASE 11 22 33 MONEY BAD PRODUCT NOT COMING OUT
        elif info == 11:
            background.pause()
            temp = vlc.MediaPlayer("miss_10.mp3")
            temp.play()
            temp.audio_set_volume(100)
            time.sleep(4)
            temp.stop()
            background.pause()
            led_lock.acquire(True)
            GPIO.output(money_bad_led, GPIO.LOW)
            led_lock.release()
        elif info == 22:
            background.pause()
            if money >= 10:
                temp = vlc.MediaPlayer("miss_10.mp3")
                temp.play()
                temp.audio_set_volume(100)
                time.sleep(4)
                temp.stop()
                led_lock.acquire(True)
                GPIO.output(money_bad_led, GPIO.LOW)
                led_lock.release()
            else:
                temp = vlc.MediaPlayer("miss_20.mp3")
                temp.play()
                temp.audio_set_volume(100)
                time.sleep(4)
                temp.stop
                led_lock.acquire(True)
                GPIO.output(money_bad_led, GPIO.LOW)
                led_lock.release()
            background.pause()
        elif info == 33:
            background.pause()
            if money >= 20:
                temp = vlc.MediaPlayer("miss_10.mp3")
                temp.play()
                temp.audio_set_volume(100)
                time.sleep(4)
                temp.stop()
                led_lock.acquire(True)
                GPIO.output(money_bad_led, GPIO.LOW)
                led_lock.release()
            elif money >= 10:
                temp = vlc.MediaPlayer("miss_20.mp3")
                temp.play()
                temp.audio_set_volume(100)
                time.sleep(4)
                temp.stop()
                led_lock.acquire(True)
                GPIO.output(money_bad_led, GPIO.LOW)
                led_lock.release()
            else:
                temp = vlc.MediaPlayer("miss_30.mp3")
                temp.play()
                temp.audio_set_volume(100)
                time.sleep(4)
                temp.stop
                led_lock.acquire(True)
                GPIO.output(money_bad_led, GPIO.LOW)
                led_lock.release()
            background.pause()

        #CASE 4 SAYS THE MONEY YOU HAVE
        elif info == 4:
            background.pause()
            if money == 0:
                temp = vlc.MediaPlayer("have_0.mp3")
                temp.play()
                temp.audio_set_volume(100)
                time.sleep(5)
                temp.stop()
            elif money == 10:
                temp = vlc.MediaPlayer("have_10.mp3")
                temp.play()
                temp.audio_set_volume(100)
                time.sleep(3)
                temp.stop()
            elif money == 20:
                temp = vlc.MediaPlayer("have_20.mp3")
                temp.play()
                temp.audio_set_volume(100)
                time.sleep(3)
                temp.stop()
            elif money == 30:
                temp = vlc.MediaPlayer("have_30.mp3")
                temp.play()
                #temp.audio_set_volume(100)
                time.sleep(3)
                temp.stop()
            else:
                temp = vlc.MediaPlayer("have_more_30.mp3")
                temp.play()
                temp.audio_set_volume(100)
                time.sleep(3)
                temp.stop()
            background.pause()
        speech_lock.release()

##################################
####   OPERATIONS FUNCTIONS   ####
##################################

def motor_control(motor_queue,f):

    tid = ctypes.CDLL('libc.so.6').syscall(224)
    print('motor', tid)
    f.write("Motor Id:" + str(tid))

    while True:
        motor = motor_queue.get()
        if motor == 1:
            GPIO.output(choco_bar_motor,GPIO.HIGH)
            time.sleep(1)
            GPIO.output(choco_bar_motor,GPIO.LOW)
        elif motor == 2:
            GPIO.output(coke_motor,GPIO.HIGH)
            time.sleep(1)
            GPIO.output(coke_motor,GPIO.LOW)
        if motor == 3:
            GPIO.output(gum_motor,GPIO.HIGH)
            time.sleep(1)
            GPIO.output(gum_motor,GPIO.LOW)

def check_money(money_lock,sound_queue,f):
    global money

    tid = ctypes.CDLL('libc.so.6').syscall(224)
    print('money', tid)
    f.write("Money Id:" + str(tid))

    while True:
        t = time.time()
        if(GPIO.input(small_change)):
            money_lock.acquire(True)
            money = money + 10
            print("You Have" + str(money) + "Cents")
            money_lock.release()
            sound_queue.put(4)
            time.sleep(0.4)

        if(GPIO.input(big_change)):
            money_lock.acquire(True)
            money = money + 20
            print("You Have " + str(money) + " Cents")
            money_lock.release()
            sound_queue.put(4)
            time.sleep(0.4)

##################################
######   SPEECH FUNCTIONS   ######
##################################

#Proceses Speech Data and decides what to do
def string_processing(string_queue,sound_queue,motor_queue,money_lock,led_lock,f):

    global money

    tid = ctypes.CDLL('libc.so.6').syscall(224)
    print('string', tid)
    f.write("String Id:" + str(tid))

    while True:
        string = string_queue.get()

        #Get string
        word_list = string.split()

        # check machine vending
        if any(w == x for x in chocobar for w in word_list):
            if money >= 10:
                sound_queue.put(1)
                motor_queue.put(1)
                #UPDATE LED VALUE
                led_lock.acquire(True)
                GPIO.output(money_ok_led, GPIO.HIGH)
                led_lock.release()
                #UPDATE MONEY VALUE
                money_lock.acquire(True)
                money = money - 10
                money_lock.release()
            else:
                led_lock.acquire(True)
                GPIO.output(money_bad_led, GPIO.HIGH)
                led_lock.release()
                sound_queue.put(11)

        elif any(w == x for x in coke for w in word_list):
            if money >= 20:
                sound_queue.put(2)
                motor_queue.put(2)
                #UPDATE LED VALUE
                led_lock.acquire(True)
                GPIO.output(money_ok_led, GPIO.HIGH)
                led_lock.release()
                #UPDATE MONEY VALUE
                money_lock.acquire(True)
                money = money - 20
                money_lock.release()
            else:
                led_lock.acquire(True)
                GPIO.output(money_bad_led, GPIO.HIGH)
                led_lock.release()
                sound_queue.put(22)

        elif any(w == x for x in gum for w in word_list):
            if money >= 30:
                sound_queue.put(3)
                motor_queue.put(3)
                #UPDATE LED VALUE
                led_lock.acquire(True)
                GPIO.output(money_ok_led, GPIO.HIGH)
                led_lock.release()
                #UPDATE MONEY VALUE
                money_lock.acquire(True)
                money = money - 30
                money_lock.release()
            else:
                led_lock.acquire(True)
                GPIO.output(money_bad_led, GPIO.HIGH)
                led_lock.release()
                sound_queue.put(33)

        elif any(w == x for x in cash for w in word_list):

            sound_queue.put(4)

# listening thread
# gets all the recognized strings into a fifo queue
def listening(string_queue,speech_lock,f):

    tid = ctypes.CDLL('libc.so.6').syscall(224)
    f.write("Listen Id:" + str(tid))

    r = sr.Recognizer()
    m = sr.Microphone()

    print("\n \n \nCalibrating, please remain silent.")
    # why use this || this is redundant?
    with m as source:
        r.adjust_for_ambient_noise(source)
    print("Set minimum energy threshold to {}".format(r.energy_threshold))
    print("If Red Led is ON the machine is listening")

    while True:
        with m as source:
            t = time.time()
            GPIO.output(voice_led,GPIO.HIGH)
            audio = r.listen(source)
            speech_lock.acquire(True)
            print('source',t - time.time())
        try:
            t = time.time()
            value = r.recognize_google(audio)
            GPIO.output(voice_led,GPIO.LOW)
            print('You said \'' + value + '\'\n')
            speech_lock.release()
            string_queue.put(value)
            print('try', t - time.time())
            time.sleep(1)
        except sr.UnknownValueError:
            print("Unrecognizable noise")
            speech_lock.release()

##################################
#######    INITIAL SETUP   #######
##################################

### PIN INITIALIZATION

GPIO.cleanup()

# setup output pins
GPIO.setmode(GPIO.BOARD)

for pin in pin_outs:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
for pin in pin_ins:
    GPIO.setup(pin, GPIO.IN)

##################################
########   MAIN PROGRAM   ########
##################################

### GLOBAL VARIABLES
global money
money = 0

tid = ctypes.CDLL('libc.so.6').syscall(224)
print('main', threading.get_ident(), tid)

f = open("id.txt",'w')
f.write("Main Id:" + str(tid))

### THREAD COMMUNICATION Queues
string_queue = queue.Queue()
sound_queue = queue.Queue()
motor_queue = queue.Queue()

### THREAD COMMUNICATION Locks
speech_lock = threading.Lock()
money_lock = threading.Lock()
led_lock = threading.Lock()

### THREAD CONFIG
listening_thread = threading.Thread(name= 'listen'+str(tid), target=listening, args=(string_queue,speech_lock,f,))
str_processing_thread = threading.Thread(name= 'processing',target=string_processing, args=(string_queue,sound_queue,motor_queue,money_lock,led_lock,f,))
check_money_thread = threading.Thread(name= 'money',target=check_money, args=(money_lock,sound_queue,f,))
music_thread = threading.Thread(name= 'music',target=background_music, args=(sound_queue,speech_lock,led_lock,f,))
motor_thread = threading.Thread(name= 'motor',target=motor_control, args=(motor_queue,f,))

###THREAD INITIALIZATION

listening_thread.start()
str_processing_thread.start()
check_money_thread.start()
music_thread.start()
motor_thread.start()

listening_thread.join()
str_processing_thread.join()
check_money_thread.join()
music_thread.join()
motor_thread.join()

time.sleep(1)
f.close()
###############   END OF PROGRAM   ###############

### RECURSOS NÃO USADOS

#speaker_flag = threading.Event()
#light_flag = threading.Event()
#background_light_thread = threading.Thread(target=background_light, args=(light_flag,))
#background_light_thread.start()