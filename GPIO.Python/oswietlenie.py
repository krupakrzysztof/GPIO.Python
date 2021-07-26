import RPi.GPIO as GPIO
import time
from datetime import datetime
import fourletterphat
import threading
import w1thermsensor as w1s

# format to zapisywania godziny i daty
TIMEFORMAT = "%H:%M:%S"

class timeToRun:
    """ Czas, o którym następuje włączenie lub wyłączenie oświetlenia """
    enableHour = 0
    enableMinute = 0
    disableHour = 0
    disableMinute = 0

    def __init__(self, enableHour, enableMinute, disableHour, disableMinute):
        self.enableHour = enableHour
        self.enableMinute = enableMinute
        self.disableHour = disableHour
        self.disableMinute = disableMinute

    @property
    def getEnableSpan(self):
        """ Pobranie czasu włączenia w formacie unikalnym """
        return (self.enableHour * 60) + self.enableMinute

    @property
    def getDisableSpan(self):
        """ Pobranie czasu wyłączenia w formacie unikalnym """
        return (self.disableHour * 60) + self.disableMinute

stopClock = False

def clock():
    # ustawienie zmiennej jako globalnej dla tego wątku
    global stopClock
    isBright = True
    fourletterphat.set_brightness(5)
    while True:
        if stopClock:
            time.sleep(0.1)
            continue
        
        try:
            fourletterphat.clear()
            now = datetime.now()
            #if (now.hour * 60 + now.minute) >= 400 and (now.hour * 60 + now.minute) <= 1350:
            if (now.hour * 60 + now.minute) >= 500 and (now.hour * 60 + now.minute) <= 1350:
                if not isBright:
                    fourletterphat.set_brightness(5)
                    isBright = True
            else:
                if isBright:
                    fourletterphat.set_brightness(0)
                    isBright = False
            str_time = time.strftime("%H%M")
            fourletterphat.print_number_str(str_time)
            fourletterphat.set_decimal(1, int(time.time() % 2))
            fourletterphat.show()
            time.sleep(0.1)
        except:
            time.sleep(0.1)


def showTemperature():
    # ustawienie pinu 26 jako wejście
    GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # ustawienie zmiennej jako globalnej dla tego wątku
    global stopClock
    # inicjacja czujnika temperatury
    sensor = w1s.W1ThermSensor()
    while True:
        # czekanie na naciśnięcie przycisku
        GPIO.wait_for_edge(26, GPIO.FALLING)
        # wyłączenie zegarka
        stopClock = True
        fourletterphat.clear()
        # wyświetlenie odczytanej temperatury
        fourletterphat.print_str(str(round(sensor.get_temperature() * 10)) + 'C')
        fourletterphat.set_decimal(1, True)
        fourletterphat.show()
        # odczekanie 5 sekund
        time.sleep(5)
        # wznowienie zegarka
        stopClock = False

now = datetime.now()
nowSpan = (now.hour * 60) + now.minute
enabled = False

enableTimes = [ 
   timeToRun(7, 0, 22, 30), # poniedziałek
   timeToRun(7, 0, 22, 30), # wtorek
   timeToRun(7, 0, 22, 30), # środa
   timeToRun(7, 0, 22, 30), # czwartek
   timeToRun(7, 0, 21, 0), # piątek
   timeToRun(4, 30, 21, 0), # sobota
   timeToRun(4, 30, 22, 30) # niedziela
    ]

print(now.strftime(TIMEFORMAT) + ' Zaczynam działanie')

GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.OUT, initial=GPIO.HIGH)

# uruchomienie wątku odpowiedzialnego za zegarek
threading.Thread(target=clock).start()
# uruchomienie wątku odpowiedzialnego za odczytwanie temperatury
threading.Thread(target=showTemperature).start()

while True:
    timeToRunNow = enableTimes[datetime.isoweekday(now) - 1]
    if (nowSpan >= timeToRunNow.getEnableSpan and nowSpan <= timeToRunNow.getDisableSpan):
        if not enabled:
            GPIO.output(16, GPIO.LOW)
            print(now.strftime(TIMEFORMAT) + ' Włączam światło')
            enabled = True
    else:
        if enabled:
            GPIO.output(16, GPIO.HIGH)
            print(now.strftime(TIMEFORMAT) + ' Wyłączam światło')
            enabled = False

    # poczekanie 20 sekund przed ponownym uruchomieniem pętli
    time.sleep(20)
    now = datetime.now()
    nowSpan = (now.hour * 60) + now.minute
