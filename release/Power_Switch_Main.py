
VERSION = "V1.00c"


import machine
import binascii
from machine import UART
from umqtt.simple import MQTTClient
import _thread
import utime, time
import network
import ujson
from machine import SPI, Pin, Timer
import gc

from machine import WDT

# Based on 2024/1/15_V1.00a, Sam
# 2024/1/17 V1.00c 修正state為空值時的問題, Sam 


# 定義狀態類型
class MainStatus:
    NONE_WIFI = 0  # 還沒連上WiFi
    NONE_INTERNET = 1  # 連上WiFi，但還沒連上外網      現在先不做這個判斷
    NONE_MQTT = 2  # 連上外網，但還沒連上MQTT Broker
    NONE_FEILOLI = 3  # 連上MQTT，但還沒連上FEILOLI娃娃機(無娃娃機正常狀態)
    STANDBY_FEILOLI = 4  # 連上FEILOLI娃娃機，正常運行中(無娃娃機，不使用)
    WAITING_FEILOLI = 5  # 連上FEILOLI娃娃機，等待娃娃機回覆(無娃娃機，不使用)
    GOING_TO_OTA = 6  # 接收到要OTA，但還沒完成OTA
    UNEXPECTED_STATE = -1


# 定義狀態機類別
class MainStateMachine:
    def __init__(self):
        self.state = MainStatus.NONE_WIFI
        # 以下執行"狀態機初始化"相應的操作
        print("\n\rInit, MainStatus: NONE_WIFI")
        global main_while_delay_seconds
        main_while_delay_seconds = 1
        unique_id_hex = binascii.hexlify(machine.unique_id()).decode().upper()

    def transition(self, action):
        global main_while_delay_seconds
        global card_1
        global led_color
        global led_timer
        global np

        if action == "WiFi is disconnect":
            self.state = MainStatus.NONE_WIFI
            # 以下執行"未連上WiFi後"相應的操作
            print("\n\rAction: WiFi is disconnect, MainStatus: NONE_WIFI")
            # 設置 LED 閃爍定時器 , 250ms
            led_timer.deinit()
            led_color = 4
            led_timer.init(period=250, mode=Timer.PERIODIC, callback=toggle_led)
            main_while_delay_seconds = 1

        elif self.state == MainStatus.NONE_WIFI and action == "WiFi is OK":
            self.state = MainStatus.NONE_INTERNET
            # 以下執行"連上WiFi後"相應的操作
            print("\n\rAction: WiFi is OK, MainStatus: NONE_INTERNET")
            # 設置 LED 閃爍定時器 , 250ms
            led_timer.deinit()
            led_color = 4
            led_timer.init(period=500, mode=Timer.PERIODIC, callback=toggle_led)
            main_while_delay_seconds = 1

        elif self.state == MainStatus.NONE_INTERNET and action == "Internet is OK":
            self.state = MainStatus.NONE_MQTT
            # 以下執行"連上Internet後"相應的操作
            print("\n\rAction: Internet is OK, MainStatus: NONE_MQTT")
            led_timer.deinit()
            led_color = 4
            led_timer.init(period=1000, mode=Timer.PERIODIC, callback=toggle_led)
            main_while_delay_seconds = 1

        elif self.state == MainStatus.NONE_MQTT and action == "MQTT is OK":
            self.state = MainStatus.NONE_FEILOLI
            # 以下執行"連上MQTT後"相應的操作
            print("\n\rAction: MQTT is OK, MainStatus: NONE_FEILOLI")
            card_1["status"] = "00"
            publish_MQTT_card_data(card_1, "status")
            led_timer.deinit()
            np[0] = rainbow_colors[4]
            np.write()
            main_while_delay_seconds = 10

        # elif (self.state == MainStatus.NONE_FEILOLI or self.state == MainStatus.WAITING_FEILOLI) and action == 'FEILOLI UART is OK':
        #     self.state = MainStatus.STANDBY_FEILOLI
        #     # 以下執行"連上FEILOLI娃娃機後"相應的操作
        #     print('\n\rAction: FEILOLI UART is OK, MainStatus: STANDBY_FEILOLI')
        #     main_while_delay_seconds = 10

        # elif self.state == MainStatus.STANDBY_FEILOLI and action == 'FEILOLI UART is waiting':
        #     self.state = MainStatus.WAITING_FEILOLI
        #     # 以下執行"等待FEILOLI娃娃機後"相應的操作
        #     print('\n\rAction: FEILOLI UART is waiting, MainStatus: WAITING_FEILOLI')
        #     main_while_delay_seconds = 10

        # elif self.state == MainStatus.WAITING_FEILOLI and action == 'FEILOLI UART is not OK':
        #     self.state = MainStatus.NONE_FEILOLI
        #     # 以下執行"等待失敗後"相應的操作
        #     print('\n\rAction: FEILOLI UART is not OK, MainStatus: NONE_FEILOLI')
        #     main_while_delay_seconds = 10

        elif (
            self.state == MainStatus.NONE_FEILOLI
            or self.state == MainStatus.STANDBY_FEILOLI
            or self.state == MainStatus.WAITING_FEILOLI
        ) and action == "MQTT is not OK":
            self.state = MainStatus.NONE_MQTT
            # 以下執行"MQTT失敗後"相應的操作
            print("\n\rAction: MQTT is not OK, MainStatus: NONE_MQTT")
            main_while_delay_seconds = 1

        else:
            print("\n\rInvalid action:", action, "for current state:", self.state)
            main_while_delay_seconds = 1


# 開啟 token 檔案
def load_token():
    global token
    try:
        with open("token.dat") as f:
            token = f.readlines()[0].strip()
        print("Get token:", token)
        len_token = len(token)
        if len_token != 36:
            while True:
                print("token的長度不對:", len_token)
                time.sleep(30)
    except Exception as e:
        print("Open token.dat failed:", e)
        while True:
            print("遺失 token 檔案")
            time.sleep(30)


def connect_wifi():
    global wifi
    wifi = network.WLAN(network.STA_IF)

    if not wifi.config("essid"):
        print("沒有經過wifimgr.py")
        wifi_ssid = "paypc"
        wifi_password = "abcd1234"
        wifi.active(True)
        wifi.connect(wifi_ssid, wifi_password)

    print("Start to connect WiFi, SSID : {}".format(wifi.config("essid")))

    while True:
        for i in range(20):
            print("Try to connect WiFi in {}s".format(i))
            utime.sleep(1)
            if wifi.isconnected():
                break
        if wifi.isconnected():
            print("WiFi connection OK!")
            print("Network Config=", wifi.ifconfig())
            connect_internet_data = InternetData()
            connect_internet_data.ip_address = wifi.ifconfig()[0]
            tmp_mac_address = wifi.config("mac")
            connect_internet_data.mac_address = "".join(
                ["{:02X}".format(byte) for byte in tmp_mac_address]
            )
            return connect_internet_data
        else:
            print("WiFi({}) connection Error".format(wifi.config("essid")))
            for i in range(30, -1, -1):
                print("倒數{}秒後重新連線WiFi".format(i))
                time.sleep(1)


class InternetData:
    def __init__(self):
        self.ip_address = ""
        self.mac_address = ""


# 連線MQTT Broker，如果有換網址，請修改此函式
def connect_mqtt():
    # mq_server = 'broker.MQTTGO.io'
    mq_server = "wifi.power.switch.mqtt.propskynet.com"
    mq_id = my_internet_data.mac_address
    mq_user = "user123"
    mq_pass = "user123"
    while True:
        try:
            mq_client = MQTTClient(mq_id, mq_server, user=mq_user, password=mq_pass)
            mq_client.connect()
            print("MQTT Broker connection OK!")
            return mq_client
        except Exception as e:
            print("MQTT Broker connection failed:", e)
            for i in range(10, -1, -1):
                print("倒數{}秒後重新連線MQTT Broker".format(i))
                time.sleep(1)


def subscribe_MQTT_claw_recive_callback(topic, message):
    global card_1
    print("MQTT Subscribe recive data")
    print("MQTT Subscribe topic:", topic)
    print("MQTT Subscribe data(JSON_str):", message)
    try:
        data = ujson.loads(message)
        print("MQTT Subscribe data:", data)

        macid = my_internet_data.mac_address
        mq_topic = "03ac6a6316d8fd2c7401249b6ca30a06/" + macid + "/" + token
        
        # 判斷data中是否有state，如果沒有，就加上state  # 2021/1/17 Sam
        if "state" not in data:
            data["state"] = ""

        if topic.decode() == (mq_topic + "/fota"):
            otafile = "otalist.dat"
            if ("file_list" in data) and ("password" in data):
                if data["password"] == "c0b82a2c-4b03-42a5-92cd-3478798b2a90":
                    # print("password checked")
                    publish_MQTT_card_data(card_1, "fotaack", data["state"])
                    with open(otafile, "w") as f:
                        f.write("".join(data["file_list"]))
                    print("otafile 輸出完成，即將重開機...")
                    time.sleep(3)
                    machine.reset()
                else:
                    print("password failed")
        elif topic.decode() == (mq_topic + "/commands"):
            if data["commands"] == "ping":
                publish_MQTT_card_data(card_1, "commandack-pong", data["state"])
            elif data["commands"] == "version":
                publish_MQTT_card_data(card_1, "commandack-version", data["state"])
            elif data["commands"] == "on":
                publish_MQTT_card_data(card_1, "commandack-on", data["state"])
            elif data["commands"] == "off":
                publish_MQTT_card_data(card_1, "commandack-off", data["state"])
            elif data["commands"] == "restart":
                if "seconds" in data:
                    publish_MQTT_card_data(
                        card_1, "commandack-restart", data["state"], data["seconds"]
                    )
                else:
                    publish_MQTT_card_data(card_1, "commandack-restart", data["state"])
            elif data["commands"] == "getstatus":
                publish_MQTT_card_data(card_1, "commandack-getstatus", data["state"])
            # elif data['commands'] == 'clawreboot':
            #     if 'state' in data:
            #         publish_MQTT_card_data(card_1, 'commandack-clawreboot',data['state'])
            #         uart_FEILOLI_send_packet(KindFEILOLIcmd.Send_Machine_reboot)
            # else:
            #     publish_MQTT_card_data(card_1, 'commandack-clawreboot')
            #     uart_FEILOLI_send_packet(KindFEILOLIcmd.Send_Machine_reboot)
            # elif data['commands'] == 'clawstartgame':
            #     if 'state' in data:
            #         publish_MQTT_card_data(card_1, 'commandack-clawstartgame',data['state'])
            #         epays=data['epays']
            #         freeplays=data['freeplays']
            #         uart_FEILOLI_send_packet(KindFEILOLIcmd.Send_Starting_once_game)
            # publish_MQTT_card_data(card_1, 'commandack-clawstartgame')
            # epays=['epays']
            # freeplays=['freeplays']
            # uart_FEILOLI_send_packet(KindFEILOLIcmd.Send_Starting_once_game)
    #       elif data['commands'] == 'getstatus':

    except Exception as e:
        print("MQTT Subscribe data to JSON Error:", e)


def subscribe_MQTT_claw_topic():  # MQTT_client暫時固定為mq_client_1
    mq_client_1.set_callback(subscribe_MQTT_claw_recive_callback)
    macid = my_internet_data.mac_address
    mq_topic = "03ac6a6316d8fd2c7401249b6ca30a06/" + macid + "/" + token + "/commands"

    mq_client_1.subscribe(mq_topic)
    print("MQTT Subscribe topic:", mq_topic)
    mq_topic = "03ac6a6316d8fd2c7401249b6ca30a06/" + macid + "/" + token + "/fota"
    mq_client_1.subscribe(mq_topic)
    print("MQTT Subscribe topic:", mq_topic)


def publish_data(mq_client, topic, data):
    try:
        # mq_message = ujson.dumps(data)
        print("MQTT Publish topic:", topic)
        print("MQTT Publish data(JSON_str):", data)
        mq_client.publish(topic, data)
        print("MQTT Publish Successful")
    except Exception as e:
        print("MQTT Publish Error:", e)
        now_main_state.transition("MQTT is not OK")


def publish_MQTT_card_data(
    card_data, MQTT_API_select, para1="", para2=""
):  # 可以選擇card_1、claw_2、...，但MQTT_client暫時固定為mq_client_1
    global gCommandOn, gCommandOff, gCommandRestart
    global now_main_state
    if MQTT_API_select == "commandack-getstatus" or MQTT_API_select == "status":
        macid = my_internet_data.mac_address
        mq_topic = "03ac6a6316d8fd2c7401249b6ca30a06/" + macid + "/" + token + "/status"
        if para1 == "":
            MQTT_card_data = {
                "status": card_data["status"],
                # 如果card_data["Power_EN"] == 1，代表5V和12V都有輸出, mode = "on"，否則 mode = "off"
                "mode": "on" if card_data["Power_EN"] == 1 else "off",
                "wifirssi": card_data["RSSI"],
                "time": utime.time(),
            }
        else:
            MQTT_card_data = {
                "status": card_data["status"],
                # 如果card_data["Power_EN"] == 1，代表5V和12V都有輸出, mode = "on"，否則 mode = "off"
                "mode": "on" if card_data["Power_EN"] == 1 else "off",
                "wifirssi": card_data["RSSI"],
                "time": utime.time(),
                "state": para1,
            }

    elif MQTT_API_select == "commandack-pong":
        macid = my_internet_data.mac_address
        mq_topic = (
            "03ac6a6316d8fd2c7401249b6ca30a06/" + macid + "/" + token + "/commandack"
        )
        if para1 == "":
            MQTT_card_data = {"ack": "pong", "time": utime.time()}
        else:
            MQTT_card_data = {"ack": "pong", "state": para1, "time": utime.time()}
    elif MQTT_API_select == "commandack-version":
        macid = my_internet_data.mac_address
        mq_topic = (
            "03ac6a6316d8fd2c7401249b6ca30a06/" + macid + "/" + token + "/commandack"
        )
        if para1 == "":
            MQTT_card_data = {"ack": VERSION, "time": utime.time()}
        else:
            MQTT_card_data = {"ack": VERSION, "state": para1, "time": utime.time()}

    elif MQTT_API_select == "fotaack":
        macid = my_internet_data.mac_address
        mq_topic = (
            "03ac6a6316d8fd2c7401249b6ca30a06/" + macid + "/" + token + "/fotaack"
        )
        if para1 == "":
            MQTT_card_data = {"ack": "OK", "time": utime.time()}
        else:
            MQTT_card_data = {"ack": "OK", "state": para1, "time": utime.time()}
    elif MQTT_API_select == "commandack-on":
        macid = my_internet_data.mac_address
        mq_topic = (
            "03ac6a6316d8fd2c7401249b6ca30a06/" + macid + "/" + token + "/commandsack"
        )
        gCommandOn = 1
        if para1 == "":
            MQTT_card_data = {"ack": "on", "time": utime.time()}
        else:
            MQTT_card_data = {"ack": "on", "state": para1, "time": utime.time()}

    elif MQTT_API_select == "commandack-off":
        macid = my_internet_data.mac_address
        mq_topic = (
            "03ac6a6316d8fd2c7401249b6ca30a06/" + macid + "/" + token + "/commandack"
        )
        gCommandOff = 1
        if para1 == "":
            MQTT_card_data = {"ack": "off", "time": utime.time()}
        else:
            MQTT_card_data = {"ack": "off", "state": para1, "time": utime.time()}
    elif MQTT_API_select == "commandack-restart":
        macid = my_internet_data.mac_address
        mq_topic = (
            "03ac6a6316d8fd2c7401249b6ca30a06/" + macid + "/" + token + "/commandack"
        )

        if para1 == "":
            MQTT_card_data = {"ack": "restart", "time": utime.time()}
        else:
            MQTT_card_data = {"ack": "restart", "state": para1, "time": utime.time()}
        if para2 == "":
            # 執行三秒的重開關
            gCommandRestart = 3

        else:
            # 執行para2秒的重開關
            gCommandRestart = para2
    mq_json_str = ujson.dumps(MQTT_card_data)
    publish_data(mq_client_1, mq_topic, mq_json_str)


server_report_sales_period = 60 * 60  # 3分鐘 = 3*60 單位秒
# server_report_sales_period = 10   # For快速測試
server_report_sales_counter = 0  # -1代表第一次執行就要執行，0代表第一次執行不要執行


# 定義server_report計時器回調函式 (每1秒執行1次)
def server_report_timer_callback(timer):
    global card_1, wdt, mq_client_1
    if (
        now_main_state.state == MainStatus.NONE_FEILOLI
        or now_main_state.state == MainStatus.STANDBY_FEILOLI
        or now_main_state.state == MainStatus.WAITING_FEILOLI
    ):
        try:
            # 更新 MQTT Subscribe
            mq_client_1.check_msg()
            # mq_client_1.ping()
        except OSError as e:
            print("WiFi is disconnect")
            now_main_state.transition("WiFi is disconnect")
            mq_client_1.disconnect()
            return

        global server_report_sales_counter
        server_report_sales_counter = (
            server_report_sales_counter + 1
        ) % server_report_sales_period
        if server_report_sales_counter == 0:
            # wdt.feed()
            # publish_MQTT_card_data(card_1, 'sales')
            # if card_1.Error_Code_of_Machine != 0x00 :
            publish_MQTT_card_data(card_1, "status")


def get_wifi_signal_strength(wlan):
    if wlan.isconnected():
        signal_strength = wlan.status("rssi")
        return signal_strength
    else:
        return None


def toggle_led(timer):
    global led_color
    if np[0] == rainbow_colors[led_color]:
        np[0] = rainbow_colors[7]
    else:
        np[0] = rainbow_colors[led_color]
    np.write()


def UDP_Load_Wifi():
    global led_color
    # Connect to Wi-Fi
    wifi_ssid = "Sam"
    wifi_password = "0928666624"

    unique_id_hex = binascii.hexlify(machine.unique_id()[-3:]).decode().upper()

    DHCP_NAME = "Power_" + unique_id_hex

    station = network.WLAN(network.STA_IF)
    station.active(True)
    # 判斷是否已經連上WiFi
    if station.isconnected():
        station.disconnect()

    station.config(dhcp_hostname=DHCP_NAME)
    station.connect(wifi_ssid, wifi_password)

    led_timer.deinit()
    led_color = 2
    led_timer.init(period=500, mode=Timer.PERIODIC, callback=toggle_led)

    while not station.isconnected():
        pass

    led_timer.deinit()
    led_color = 2
    led_timer.init(period=1000, mode=Timer.PERIODIC, callback=toggle_led)

    print("Connected to Wi-Fi")
    print("\nConnected. Network config: ", station.ifconfig())

    # Set up UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("0.0.0.0", 1234))

    print("Listening for UDP messages on port 1234")

    while True:
        data, addr = udp_socket.recvfrom(1024)
        print("Received message: {}".format(data.decode("utf-8")))

        with open("wifi.dat", "w") as f:
            f.write(data.decode("utf-8"))

        # 連接成功，綠色常亮
        np[0] = rainbow_colors[2]
        np.write()

        # 停止 LED 閃爍定時器
        led_timer.deinit()

        sleep(3)

        machine.reset()


############################################# 初始化 #############################################

# 開啟 token 檔案
load_token()

wifi = network.WLAN(network.STA_IF)


print("1開機秒數:", time.ticks_ms() / 1000)
wdt = WDT(timeout=1000 * 60 * 10)
print("2開機秒數:", time.ticks_ms() / 1000)


# 創建狀態機
now_main_state = MainStateMachine()

# 創建 MQTT Client 1 資料
mq_client_1 = None


# 定義IO口
IO_SW1_PIN = 0  # 輕觸按鍵
IO_5V_EN_PIN = 16  # 控制5V輸出的IO
IO_12V_EN_PIN = 2  # 控制12V輸出的IO

# 初始化IO
IO_SW1 = Pin(IO_SW1_PIN, Pin.IN)
IO_5V_EN = Pin(IO_5V_EN_PIN, Pin.OUT)
IO_12V_EN = Pin(IO_12V_EN_PIN, Pin.OUT)

# 初始狀態設定
IO_5V_EN.value(1)
IO_12V_EN.value(1)
Power_EN = 1

# 定義WS2812的參數
NUM_LEDS = 1
PIN = 5  # 這是WS2812數據輸入的引腳

# 初始化WS2812
np = neopixel.NeoPixel(machine.Pin(PIN), NUM_LEDS)

# 定義彩虹顏色
rainbow_colors = [
    (255, 0, 0),  # 紅色
    (255, 127, 0),  # 橙色
    (255, 255, 0),  # 黃色
    (0, 255, 0),  # 綠色
    (0, 0, 128),  # 藍色
    (75, 0, 130),  # 靛色
    (148, 0, 211),  # 紫色
    (0, 0, 0),  # 黑色
    (255, 255, 255),  # 白色
]

# 設置 LED 閃爍定時器
led_timer = Timer(1)
led_color = 4
led_timer.init(period=250, mode=Timer.PERIODIC, callback=toggle_led)


# 創建計時器物件
server_report_timer = machine.Timer(0)
# 設定server_report計時器的間隔和回調函式
TIMER_INTERVAL = 1000  # 設定1秒鐘 = 1000（單位：毫秒）
server_report_timer.init(
    period=TIMER_INTERVAL,
    mode=machine.Timer.PERIODIC,
    callback=server_report_timer_callback,
)

last_time = 0
main_while_delay_seconds = 1

# 初始化 card_1 dict 資料
# 包裝現在輸出的狀態
# WIFI的RSSI
# WIFI的IP
card_1 = {"Power_EN": 0, "RSSI": 0, "status": "00"}


# 主程式迴圈
# 每100ms執行一次
# 每1秒執行一次狀態機
# 檢查gCommandOn,gCommandOff,gCommandRestart，來控制5v和12v的開關
# 當按下io_sw1時，執行5v和12v的toggle
# 當長按io_sw1時，執行重設wifi ssid的功能
gCommandOn = 0
gCommandOff = 0
gCommandRestart = 0

longPressTimer = 0

while True:
    utime.sleep_ms(100)
    current_time = time.ticks_ms()

    if gCommandOn == 1:
        gCommandOn = 0
        IO_5V_EN.value(1)
        IO_12V_EN.value(1)
        Power_EN = 1
        print("5V and 12V ON")

    if gCommandOff == 1:
        gCommandOff = 0
        IO_5V_EN.value(0)
        IO_12V_EN.value(0)
        Power_EN = 0
        print("5V and 12V OFF")

    if gCommandRestart > 0:
        delayTime = gCommandRestart
        gCommandRestart = 0
        IO_5V_EN.value(0)
        IO_12V_EN.value(0)
        Power_EN = 0
        print("5V and 12V OFF")
        print("等待", delayTime, "秒")
        time.sleep(delayTime)
        IO_5V_EN.value(1)
        IO_12V_EN.value(1)
        Power_EN = 1
        print("5V and 12V ON")

    if IO_SW1.value() == 0:  # 按鍵被按下
        if longPressTimer == 0:
            print("按鍵被按下")
            if Power_EN == 0:
                Power_EN = 1
                IO_5V_EN.value(Power_EN)
                IO_12V_EN.value(Power_EN)
                print("5V and 12V ON")
            else:
                Power_EN = 0
                IO_5V_EN.value(Power_EN)
                IO_12V_EN.value(Power_EN)
                print("5V and 12V OFF")
        # 檢查是否長按io_sw1
        longPressTimer = longPressTimer + 1
        if longPressTimer > 50:  # 長按io_sw1，超過5秒
            # 長按io_sw1
            print("長按io_sw1")
            server_report_timer.deinit()
            led_timer.deinit()
            UDP_Load_Wifi()
    else:
        longPressTimer = 0

    if time.ticks_diff(current_time, last_time) >= main_while_delay_seconds * 1000:
        last_time = time.ticks_ms()

        wdt.feed()

        card_1["Power_EN"] = Power_EN
        card_1["RSSI"] = get_wifi_signal_strength(wifi)

        if now_main_state.state == MainStatus.NONE_WIFI:
            print("\n\rnow_main_state: WiFi is disconnect, 開機秒數:", current_time / 1000)

            my_internet_data = connect_wifi()
            # 打印 myInternet 内容
            print("My IP Address:", my_internet_data.ip_address)
            print("My MAC Address:", my_internet_data.mac_address)
            now_main_state.transition("WiFi is OK")
            card_1["status"] = "WiFi is OK"

        elif now_main_state.state == MainStatus.NONE_INTERNET:
            print("\n\rnow_main_state: WiFi is OK, 開機秒數:", current_time / 1000)
            now_main_state.transition("Internet is OK")  # 目前不做判斷，狀態機直接往下階段跳轉

        elif now_main_state.state == MainStatus.NONE_MQTT:
            print("now_main_state: Internet is OK, 開機秒數:", current_time / 1000)
            mq_client_1 = connect_mqtt()
            if mq_client_1 is not None:
                subscribe_MQTT_claw_topic()
                now_main_state.transition("MQTT is OK")
            gc.collect()
            print(gc.mem_free())

        elif now_main_state.state == MainStatus.NONE_FEILOLI:
            print(
                "\n\rnow_main_state: MQTT is OK (FEILOLI UART is not OK), 開機秒數:",
                current_time / 1000,
            )
            gc.collect()
            print(gc.mem_free())
            print("開機秒數:", current_time / 1000)

        # elif now_main_state.state == MainStatus.STANDBY_FEILOLI:
        #     print('\n\rnow_main_state: FEILOLI UART is OK, 開機秒數:', current_time / 1000)
        #     gc.collect()
        #     print(gc.mem_free())

        # elif now_main_state.state == MainStatus.WAITING_FEILOLI:
        #     print('\n\rnow_main_state: FEILOLI UART is witing, 開機秒數:', current_time / 1000)
        #     gc.collect()
        #     print(gc.mem_free())

        else:
            print("\n\rInvalid action! now_main_state:", now_main_state.state)
            print("開機秒數:", current_time / 1000)

    # 获取当前时间戳
    timestamp = utime.time()
    # 转换为本地时间
    local_time = utime.localtime(timestamp)
    # 格式化为 "mm/dd hh:mm" 格式的字符串
    formatted_time = "{:02d}/{:02d} {:02d}:{:02d}".format(
        local_time[1], local_time[2], local_time[3], local_time[4]
    )

