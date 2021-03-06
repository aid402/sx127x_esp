#import esp
#esp.osdebug(None)
import gc
from machine import Pin
import time
#import utime
import network
#import socket
#import framebuf
import sx127x
gc.collect()

# setup Wi-Fi network
import network
sta_if = network.WLAN(network.STA_IF)
sta_ap = network.WLAN(network.AP_IF)
sta_if.active(False) # off Wi-Fi interface
sta_ap.active(False) # off Wi-Fi access point

wifi = 0 # 0 - off, 1 - create AP, 2 - connect to AP

if wifi == 0:
    # Wi-Fi off
    sta_if.active(False)
    sta_ap.active(False)

elif wifi == 1:
    # create AP
    sta_if.active(False)
    sta_ap.active(True)
    sta_ap.config(essid="esp-net", authmode=network.AUTH_WPA_WPA2_PSK, password="********")
    # IP address, netmask, gateway, DNS
    sta_ap.ifconfig(['192.168.1.1', '255.255.255.0', '192.168.1.1', '8.8.8.8'])

elif wifi == 2:
    # connnect to AP
    sta_ap.active(False)
    sta_if.active(True)
    sta_if.connect('veonet', '********')
    sta_if.ifconfig(['192.168.0.13', '255.255.255.0', '192.168.0.254', '192.168.0.254'])
    #sta_if.ifconfig()


def on_receive(tr, payload, crcOk):
    tr.blink()
    payload_string = payload.decode()
    rssi = tr.getRSSI()
    snr  = tr.getSNR()
    print("*** Received message ***\n{}".format(payload_string))
    print("crcOk={}, RSSI={}, SNR={}\n".format(crcOk, rssi, snr))


# init SX127x RF module
#tr = sx127x.RADIO(mode=sx127x.LORA)
#tr = sx127x.RADIO(mode=sx127x.FSK)
tr = sx127x.RADIO(mode=sx127x.OOK)

tr.setFrequency(434000,000) # kHz, Hz
tr.setPower(17, True)       # power +17dBm (RFO pin if False or PA_BOOST pin if True)
tr.setHighPower(True)       # add +3 dB (up to +20 dBm power on PA_BOOST pin)
tr.setOCP(240, True)        # set OCP trimming (> 120 mA if High Power is on)
tr.enableCRC(True, True)    # CRC=on (CrcAutoClearOff=on in FSK/OOK mode)

if tr.isLora(): # LoRa mode
    tr.setBW(125.)    # BW: 7.8...500 kHz
    tr.setSF(10)      # SF: 6...12
    tr.setLDRO(False) # Low Datarate Optimize
    tr.setCR(5)       # CR: 5..8
    tr.setPreamble(8) # 6..65535 (8 by default)
    tr.setSW(0x12)    # SW allways 0x12

else: # FSK/OOK mode
    tr.setBitrate(4800)    # bit/s
    tr.setFdev(5000.)      # frequency deviation [Hz] 
    tr.setRxBW(10.4)       # 2.6...250 kHz
    tr.setAfcBW(2.6)       # 2.6...250 kHz
    tr.setFixedLen(False)  # fixed packet size or variable
    tr.enableAFC(False)    # AFC on/off
    tr.setDcFree(2)        # 0=Off, 1=Manchester, 2=Whitening

tr.collect()

# LOOK HERE and CHANGE!!!
#MODE = 0 # do nothing
#MODE = 1 # transmitter
#MODE = 2 # reseiver
MODE = 3 # morse transmitter in continuous mode

if MODE == 1:
    # transmitter
    while True:
        tr.blink()
        tr.send("Hello!")
        time.sleep_ms(3000)

elif MODE == 2:
    # reseiver
    tr.onReceive(on_receive) # set the receive callback
    tr.receive() # go into receive mode
    time.sleep(-1) # wait interrupt


msg = "-- --- ..." # "MOS"
pause   = 2000 # ms
t_pause = 150  # ms
t_dot   = 150  # ms
t_line  = 450  # ms
t_space = 450  # ms

if MODE == 0 or MODE == 3:
    DATA = Pin(16, Pin.OUT) # DIO2/DATA
    #DCLK = Pin(0, Pin.IN)  # DIO1/DCLK

def data(value=1):
    DATA.value(value)
    tr.led(value)

def delay(ms):
    time.sleep_ms(ms)

def morse_send(msg):
    tr.tx(True)
    for c in msg:
        if c == '.':
            data(1)
            delay(t_dot)
            data(0)
            delay(t_pause)
        elif c == '-':
            data(1)
            delay(t_line)
            data(0)
            delay(t_pause)
        elif c == ' ':
            data(0)
            delay(t_space)
    tr.tx(False)


if MODE == 3:
    # morse transmitter in continuous FSK/OOK mode
    tr.init(mode=sx127x.OOK)
    #tr.ook()
    #tr.fsk()
    tr.continuous()
    while True:
        morse_send(msg)
        delay(pause)

elif MODE == 0:
    # do "nothing"
    tr.init(mode=sx127x.OOK)
    #tr.ook()
    tr.continuous()


