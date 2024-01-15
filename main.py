from machine import Pin, Timer
import machine
import neopixel
import time
import network

# 定義IO口
IO_SW1_PIN = 0   # 輕觸按鍵
IO_5V_EN_PIN = 16  # 控制5V輸出的IO
IO_12V_EN_PIN = 2  # 控制12V輸出的IO

# 初始化IO
IO_SW1 = Pin(IO_SW1_PIN, Pin.IN)
IO_5V_EN = Pin(IO_5V_EN_PIN, Pin.OUT)
IO_12V_EN = Pin(IO_12V_EN_PIN, Pin.OUT)

# 初始狀態設定
IO_5V_EN.value(0)
IO_12V_EN.value(0)
Power_EN = 0

# 定義WS2812的參數
NUM_LEDS = 1
PIN = 5  # 這是WS2812數據輸入的引腳

# 初始化WS2812
np = neopixel.NeoPixel(machine.Pin(PIN), NUM_LEDS)

# 定義彩虹顏色
rainbow_colors = [
    (255, 0, 0),    # 紅色
    (255, 127, 0),  # 橙色
    (255, 255, 0),  # 黃色
    (0, 255, 0),    # 綠色
    (0, 0, 255),    # 藍色
    (75, 0, 130),   # 靛色
    (148, 0, 211),   # 紫色
    (0, 0, 0),       # 黑色
    (255, 255, 255) # 白色
]
rainbow_colors_count = len(rainbow_colors)
color = rainbow_colors_count-1

# 初始化 開機輸出，led綠閃0.5S，連線wifi，辨斷長按

Power_EN = 1
IO_5V_EN.value(Power_EN)
IO_12V_EN.value(Power_EN)

# 定義變數
wifi_connected = False
reset_timer = 0

def toggle_led(timer):
    global led_color
    if np[0] == rainbow_colors[led_color] :
        np[0]=rainbow_colors[7]
    else :
        np[0]=rainbow_colors[led_color]
    np.write()


def check_wifi(timer):
    global wifi_connected
    if wlan.isconnected():
        wifi_connected = True
        timer.deinit()


# 設置 LED 閃爍定時器
led_timer = Timer(0)
led_color=3
led_timer.init(period=500, mode=Timer.PERIODIC, callback=toggle_led)


# Wi-Fi 設定
ssid = "Sam&Betty"
password = "0928666624"

# Wi-Fi 連接
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    wlan.connect(ssid, password)

# 設置檢查 Wi-Fi 連接定時器
wifi_check_timer = Timer(1)
wifi_check_timer.init(period=1000, mode=Timer.PERIODIC, callback=check_wifi)


# 主迴圈
while not wifi_connected:
    if IO_SW1.value() == 0:  # 按鍵被按下
        reset_timer += 1
    else:
        reset_timer = 0

    if reset_timer >= 5:  # 按鍵長按超過 5 秒
        print("進入 WiFi 重置模式")
        wlan.disconnect()
        wlan.active(False)
        break

    time.sleep(0.1)  # 小睡 0.1 秒以減少 CPU 負擔

print("wifi OK")
np[0]=rainbow_colors[3]
np.write()
# 停止 LED 閃爍定時器
led_timer.deinit()

# 停止 Wi-Fi 連接檢查定時器
wifi_check_timer.deinit()



while True:
   
    if IO_SW1.value() == 0: # 按鍵按下
        # 按一次，Power_EN反轉
        Power_EN = 1-Power_EN
        IO_5V_EN.value(Power_EN)
        IO_12V_EN.value(Power_EN)
        # 等待按鍵釋放
        while IO_SW1.value() == 0:    
            # 持續一段時間，這裡是0.1秒
            time.sleep(0.1)

    else:    # 按鍵放開 
 
        color = color + 1
        if color == rainbow_colors_count:
            color = 0
            
        # 依次設置每個LED的顏色
        #np[0] = rainbow_colors[color]
        #np.write()

        # 持續一段時間，這裡是0.5秒
        time.sleep(0.5)