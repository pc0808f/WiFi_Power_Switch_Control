# WiFi_Power_Switch_Control
這是用來控制IPC電源的控制版

一共有控制了
一個按鍵
一組電源MOS。5V和12V 各二個控制腳
一個WS2812LED

### 有以下功能
1. 連接WIFI
2. 可被設定WIFI
3. 連接MQTT
4. 可以由MQTT進行OTA指令
5. 可以由MQTT進行上電指令
6. 可以由MQTT進行斷電指令
7. 預設系統在電供上電後3秒才送電
8. 按鍵可以開關電。
9. 長按按鍵開機可以重設WIFI


### 燈號說明
|  燈號   | 說明  |
|  ----  | ----  |
|  綠燈0.5秒閃  | 開機上電  |
| 綠燈常亮  | 正常連到WIFI |
| 紅燈  | 連線WIFI失敗 |
| 黃燈0.5秒內  | 進入配WIFI模式 |
| 黃燈1秒閃  | 進入設完WIFI但要試著連WIFI中 |
| 黃燈常亮  | 進入OTA中 |



### 參考程式
```python
from machine import Pin
import machine
import neopixel
import time

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
        np[0] = rainbow_colors[color]
        np.write()

        # 持續一段時間，這裡是0.5秒
        time.sleep(0.5)
```



