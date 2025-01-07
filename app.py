from flask import Flask, render_template, request
import RPi.GPIO as GPIO
from time import time

app = Flask(__name__)

# GPIO pinlerini ayarla
GPIO.setmode(GPIO.BCM)
pins = {'charge': 2, 'discharge': 3, 'power': 4}
for pin in pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Pin durumlarını sakla
pin_states = {key: False for key in pins}

# Timer ve charge zamanlaması
charge_start_time = None  # Charge başlangıç zamanını tutacak
charge_timer_active = False  # Charge'ın aktif olup olmadığını tutar
wait_time =600 # 600 olmali (10dakika)
@app.route('/')
def index():
    return render_template('index.html', pin_states=pin_states)

@app.route('/toggle/<pin_name>', methods=['GET'])
def toggle_pin(pin_name):
    global pin_states, charge_timer_active, charge_start_time

    if pin_name == "charge":
        if pin_states['charge']:
            # Charge'ı kapat
            pin_states['charge'] = False
            charge_timer_active = False
            charge_start_time = None  # Zamanı sıfırla
            GPIO.output(pins['charge'], GPIO.LOW)
        else:
            # Charge'ı başlat
            pin_states['charge'] = True
            charge_timer_active = True
            charge_start_time = time()  # Charge başlangıç zamanını kaydet
            GPIO.output(pins['charge'], GPIO.HIGH)

    elif pin_name == "discharge":
        if pin_states['discharge']:
            # Discharge'ı kapat
            pin_states['discharge'] = False
            GPIO.output(pins['discharge'], GPIO.LOW)  # LOW seviyesine çek
        else:
            # Eğer Charge aktifse, Discharge aktif edilemez
            if not pin_states['charge']:
                pin_states['discharge'] = True
                GPIO.output(pins['discharge'], GPIO.HIGH)  # HIGH seviyesine çek

    elif pin_name == "power":
        # Power yalnızca charge tamamlandıktan sonra açılabilir
        if pin_states['power']:
            pin_states['power'] = False
            GPIO.output(pins['power'], GPIO.LOW)  # Power'ı kapat
        else:
            # Eğer charge kapatılmış ama tamamlanmamışsa power açılamaz
            if pin_states['charge'] and charge_timer_active:
                if charge_start_time is not None:
                    elapsed_time = time() - charge_start_time
                    if elapsed_time >= wait_time:  # wait_time tamamlanmışsa açılabilir
                        pin_states['power'] = True
                        GPIO.output(pins['power'], GPIO.HIGH)  # Power'ı aç

    return {'status': 'success', 'pin_states': pin_states}


if __name__ == '__main__':
    try:
        app.run(host='192.168.1.17', port=5000, debug=True)
    except KeyboardInterrupt:
        GPIO.cleanup()
