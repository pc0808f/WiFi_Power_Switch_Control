from machine import Pin, Timer
import machine
import neopixel
import time
from time import sleep
import network
import wifimgr
from machine import WDT
import ntptime
import os

try:
    import usocket as socket
except:
    import socket

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
        

def tw_ntp(host='clock.stdtime.gov.tw', must=False):
  """
  host: 台灣可用的 ntp server 如下可任選，未指定預設為 clock.stdtime.gov.tw
    tock.stdtime.gov.tw
    watch.stdtime.gov.tw
    time.stdtime.gov.tw
    clock.stdtime.gov.tw
    tick.stdtime.gov.tw
  must: 是否非對到不可
  """ 
  ntptime.NTP_DELTA = 3155673600 # UTC+8 的 magic number
  ntptime.host = host
  count = 1
  if must:
    count = 100
  for _ in  range(count):
    try:
      ntptime.settime()
    except:
      sleep(1)
      continue
    else:
      return True
  return False

def UDP_Load_Wifi():
    global led_color
    # Connect to Wi-Fi
    wifi_ssid = "Sam"
    wifi_password = "0928666624"

    station = network.WLAN(network.STA_IF)
    station.active(True)
    
    # 判斷wifi是否在connecting，如果是，就不要再連接了
    if station.isconnected():
        station.disconnect()
        
    station.connect(wifi_ssid, wifi_password)

    led_timer.deinit()
    led_color=2
    led_timer.init(period=500, mode=Timer.PERIODIC, callback=toggle_led)

    while not station.isconnected():
        pass


    led_timer.deinit()
    led_color=2
    led_timer.init(period=1000, mode=Timer.PERIODIC, callback=toggle_led)


    print("Connected to Wi-Fi")
    print('\nConnected. Network config: ', station.ifconfig())

    # Set up UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("0.0.0.0", 1234))

    print("Listening for UDP messages on port 1234")

    while True:
        data, addr = udp_socket.recvfrom(1024)
        print("Received message: {}".format(data.decode('utf-8')))

        with open('wifi.dat', "w") as f:
            f.write(data.decode('utf-8'))


        # 連接成功，綠色常亮
        np[0]=rainbow_colors[2]
        np.write()

        # 停止 LED 閃爍定時器
        led_timer.deinit()
            
        sleep(3)
        
        machine.reset()


# 設置 LED 閃爍定時器
led_timer = Timer(0)
led_color=3
led_timer.init(period=500, mode=Timer.PERIODIC, callback=toggle_led)


# Wi-Fi 設定 讀取wifi.dat
profiles = wifimgr.read_profiles()

# Wi-Fi 連接

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    # 判斷wifi是否在connecting，如果是，就不要再連接了
    if wlan.status() == network.STAT_CONNECTING:
        # 就不要再連接了
        wlan.disconnect()
    wlan.connect(profiles["name"], profiles[profiles["name"]])

# 印出連接中的訊息，印出SSID
print("連接中...")
print(profiles["name"])


# 設置檢查 Wi-Fi 連接定時器
wifi_check_timer = Timer(1)
wifi_check_timer.init(period=1000, mode=Timer.PERIODIC, callback=check_wifi)


# 檢查WIFI的主迴圈
while not wifi_connected:
    if IO_SW1.value() == 0:  # 按鍵被按下
        reset_timer += 1
    else:
        reset_timer = 0

    if reset_timer >= 50:  # 按鍵長按超過 5 秒
        print("進入 WiFi 重置模式")
        wlan.disconnect()
        UDP_Load_Wifi()
        break

    time.sleep(0.1)  # 小睡 0.1 秒以減少 CPU 負擔

print("wifi OK")

# 暫停 3 秒，讓使用者有時間中斷程式
sleep(3)

# 打開WDT，週期5分鐘
print("打開WDT，週期5分鐘")
wdt=WDT(timeout=1000*60*5) 

# 連接成功，綠色常亮
np[0]=rainbow_colors[3]
np.write()

# 停止 LED 閃爍定時器
led_timer.deinit()

# 停止 Wi-Fi 連接檢查定時器
wifi_check_timer.deinit()

# 取得時間
tw_ntp(must=True)

# 取得網路和時間後，開始進入OTA判斷
# 檔案名稱
filename = 'otalist.dat'

# 取得目錄下的所有檔案和資料夾
file_list = os.listdir()

# 印出所有檔案和資料夾清單
print(file_list)

# 檢查檔案是否存在
if filename in file_list:
    # 在這邊要做讀取OTA列表，然後進行OTA的執行
    print("OTA檔案存在")
    
    # 黃色代表OTA執行中
    np[0]=rainbow_colors[2]
    np.write()

    try:
        with open(filename) as f:
            lines = f.readlines()[0].strip()

        lines = lines.replace(' ', '')

        # 移除字串中的雙引號和空格，然後使用逗號分隔字串
        file_list = [file.strip('"') for file in lines.split(',')]

        OTA = senko.Senko(
            user="pc0808f",  # Required
            repo="WiFi_Power_Switch_Control",  # Required
            branch="main",  # Optional: Defaults to "master"
            working_dir="release",  # Optional: Defaults to "app"
            files=file_list
        )

        # 這邊要做OTA的執行，如果置成功，就會進行重啟，如果失敗，就要重新執行
        while True:
            if OTA.update():
                print("Updated to the latest version! Rebooting...")
                os.remove(filename)
                machine.reset()
            else:
               print("Updated error! Rebooting...")

    except:
      print("Updated error! Rebooting...")
    os.remove(filename)
else:
    print("OTA檔案不存在")


print("ESP OTA OK")

print("執行Power_Switch_Main.py...")
execfile('Power_Switch_Main.py')

while True:
    try:
        print("執行Power_Switch_Main.py...")
        execfile('Power_Switch_Main.py')
    except:
        print("執行失敗，改跑Power_Switch_Main.mpy")
        __import__('Power_Switch_Main.mpy')   
