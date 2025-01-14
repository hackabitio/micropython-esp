from machine import UART, Pin
import time
from httpParser import HttpParser

ESP_OK_STATUS = "OK\r\n"
ESP_ERROR_STATUS = "ERROR\r\n"
ESP_FAIL_STATUS = "FAIL\r\n"
ESP_WIFI_CONNECTED="WIFI CONNECTED\r\n"
ESP_WIFI_GOT_IP_CONNECTED="WIFI GOT IP\r\n"
ESP_WIFI_DISCONNECTED="WIFI DISCONNECT\r\n"
ESP_WIFI_AP_NOT_PRESENT="WIFI AP NOT FOUND\r\n"
ESP_WIFI_AP_WRONG_PWD="WIFI AP WRONG PASSWORD\r\n"
ESP_BUSY_STATUS="busy p...\r\n"
UART_Tx_BUFFER_LENGTH = 1024
UART_Rx_BUFFER_LENGTH = 1024*2


class ESP:
    """
    This is a class for access ESP using AT commands
    Using this class, you access WiFi and send HTTP Post/Get requests and execute MQTT commands.
    
    Attributes:
        uartPort (int): The Uart port numbet of the RPI Pico's UART BUS [Default UART0]
        baudRate (int): UART Baud-Rate for communncating between RPI Pico's & ESP8266 [Default 115200]
        txPin (init): RPI Pico's Tx pin [Default Pin 0]
        rxPin (init): RPI Pico's Rx pin [Default Pin 1]
    """
    
    __rxData=None
    __txData=None
    __httpResponse=None
    __sendDelay=1
    
    def __init__(self, uartPort=0 ,baudRate=115200, txPin=(0), rxPin=(1)):
        """
        The constaructor for ESP class
        
        Parameters:
            uartPort (int): The Uart port numbet of the RPI Pico's UART BUS [Default UART0]
            baudRate (int): UART Baud-Rate for communncating between RPI Pico's & ESP8266 [Default 115200]
            txPin (init): RPI Pico's Tx pin [Default Pin 0]
            rxPin (init): RPI Pico's Rx pin [Default Pin 1]
        """
        self.__uartPort=uartPort
        self.__baudRate=baudRate
        self.__txPin=txPin
        self.__rxPin=rxPin
        #print(self.__uartPort, self.__baudRate, self.__txPin, self.__rxPin)
        self.__uartObj = UART(self.__uartPort, baudrate=self.__baudRate, tx=Pin(self.__txPin), rx=Pin(self.__rxPin), txbuf=UART_Tx_BUFFER_LENGTH, rxbuf=UART_Rx_BUFFER_LENGTH)
        #print(self.__uartObj)
        
    def _createHTTPParseObj(self):
        """
        Private function for creating HTTP response before executing HTTP Post/Get request
        """
        if(self.__httpResponse != None):
            del self.__httpResponse
            self.__httpResponse=HttpParser()
        else:
            self.__httpResponse=HttpParser()

    def setDelay(self, delay):
        self.__sendDelay = delay
        
    def _sendToESP(self, atCMD, delay=None):
        """
        Private function for complete ESP AT command Send/Receive operation.
        """
        self.__rxData=str()
        self.__txData=atCMD
        #print("---"+self.__txData)
        self.__uartObj.write(self.__txData)
        self.__rxData=bytes()
        
        delayTime = self.__sendDelay
        if delay != None:
            delayTime = delay
        time.sleep(delayTime)
        
        while True:
            #print(".")
            if self.__uartObj.any()>0:
                #print(self.__uartObj.any())
                break
        
        while self.__uartObj.any()>0:
            self.__rxData += self.__uartObj.read(UART_Rx_BUFFER_LENGTH)
            
        #print(self.__rxData)
        if ESP_OK_STATUS in self.__rxData:
            return self.__rxData
        elif ESP_ERROR_STATUS in self.__rxData:
            return self.__rxData
        elif ESP_FAIL_STATUS in self.__rxData:
            return self.__rxData
        elif ESP_BUSY_STATUS in self.__rxData:
            return "ESP BUSY\r\n"
        else:
            return None
        
    def startUP(self):
        """
        This funtion use to check the communication with ESP
        
        Return:
            True if communication success with the ESP
            False if unable to communication with the ESP
        """
        retData = self._sendToESP("AT\r\n")
        if(retData != None):
            if ESP_OK_STATUS in retData:
                return True
            else:
                return False
        else:
            False
    
    def reStart(self):
        """
        This funtion use to Reset the ESP
        
        Return:
            True if Reset successfully done with the ESP
            False if unable to reset the ESP
        """
        retData = self._sendToESP("AT+RST\r\n")
        if(retData != None):
            if ESP_OK_STATUS in retData:
                time.sleep(5)
                return self.startUP()
            else:
                return False
        else:
            False        
        
    
    def echoING(self, enable=False):
        """
        This function use to enable/diable AT command echo [Default set as false for diable Echo]
        
        Return:
            True if echo off/on command succefully initiate with the ESP
            False if echo off/on command failed to initiate with the ESP
        
        """
        if enable==False:
            retData = self._sendToESP("ATE0\r\n")
            if(retData != None):
                if ESP_OK_STATUS in retData:
                    return True
                else:
                    return False
            else:
                return False
        else:
            retData = self._sendToESP("ATE1\r\n")
            if(retData != None):
                if ESP_OK_STATUS in retData:
                    return True
                else:
                    return False
            else:
                return False
        
        
    def getVersion(self):
        """
        This function use to get AT command Version details
        
        Return:
            Version details on success else None
        """
        retData = self._sendToESP("AT+GMR\r\n")
        if(retData != None):
            if ESP_OK_STATUS in retData:
                #print(str(retData,"utf-8"))
                retData = str(retData).partition(r"OK")[0]
                #print(str(retData,"utf-8"))
                retData = retData.split(r"\r\n")
                retData[0] = retData[0].replace("b'","")
                retData=str(retData[0]+"\r\n"+retData[1]+"\r\n"+retData[2])
                return retData
            else:
                return None
        else:
            return None
        
    def reStore(self):
        """
        Reset the ESP into the Factory reset mode & delete previous configurations
        Return:
            True on ESP restore succesfully
            False on failed to restore ESP
        """
        retData = self._sendToESP("AT+RESTORE\r\n")
        if(retData != None):
            if ESP_OK_STATUS in retData:   
                return True
            else:
                return False
        else:
            return None
        
    def getCurrentWiFiMode(self):
        """
        Return WiFi's current mode [STA: Station, SoftAP: Software AccessPoint, or Both]
        
        Return:
            STA if ESP's wifi's current mode pre-config as Station
            SoftAP if ESP's wifi's current mode pre-config as SoftAP
            SoftAP+STA if ESP's wifi's current mode set pre-config Station & SoftAP
            None failed to detect the wifi's current pre-config mode
        """
        retData = self._sendToESP("AT+CWMODE?\r\n")
        if(retData != None):
            if "1" in retData:
                return "STA"
            elif "2" in retData:
                return "SoftAP"
            elif "3" in retData:
                return "SoftAP+STA"
            else:
                return None
        else:
            return None
        
        
    def setCurrentWiFiMode(self, mode=3):
        """
        Set WiFi's current mode [STA: Station, SoftAP: Software AccessPoint, or Both]
        
        Parameter:
            mode (int): [ 1: STA, 2: SoftAP, 3: SoftAP+STA(default)]
        
        Return:
            True on successfully set the current wifi mode
            False on failed set the current wifi mode
        
        """
        txData="AT+CWMODE="+str(mode)+"\r\n"
        retData = self._sendToESP(txData)
        if(retData!=None):
            if ESP_OK_STATUS in retData:   
                return True
            else:
                return False
        else:
            return False
        
    def getDefaultWiFiMode(self):
        """
        Get WiFi default mode [STA: Station, SoftAP: Software AccessPoint, or Both]
        
        Return:
            STA if ESP's wifi's default mode pre-config as Station
            SoftAP if ESP's wifi's default mode pre-config as SoftAP
            SoftAP+STA if ESP's wifi's default mode set pre-config Station & SoftAP
            None failed to detect the wifi's default pre-config mode
        
        """
        retData = self._sendToESP("AT+CWMODE_DEF?\r\n")
        if(retData!=None):
            if "1" in retData:
                return "STA"
            elif "2" in retData:
                return "SoftAP"
            elif "3" in retData:
                return "SoftAP+STA"
            else:
                return None
        else:
            return None
        
    def setDefaultWiFiMode(self, mode=3):
        """
        Set ESP WiFi's default mode [STA: Station, SoftAP: Software AccessPoint, or Both]
        
        Parameter:
            mode (int): ESP WiFi's [ 1: STA, 2: SoftAP, 3: SoftAP+STA(default)]
            
        Return:
            True on successfully set the default wifi mode
            False on failed set the default wifi mode
            
        """
        txData="AT+CWMODE_DEF="+str(mode)+"\r\n"
        retData = self._sendToESP(txData)
        if(retData!=None):
            if ESP_OK_STATUS in retData:   
                return True
            else:
                return False
        else:
            return False
        
    def getAvailableAPs(self):
        """
        Get available WiFi AccessPoins
        
        Retuns:
            List of Available APs or None
        """
        retData = str(self._sendToESP("AT+CWLAP\r\n"))
        if(retData != None):
            retData = retData.replace("+CWLAP:", "")
            retData = retData.replace(r"\r\n\r\nOK\r\n", "")
            retData = retData.replace(r"\r\n","@")
            retData = retData.replace("b'(","(").replace("'","")
            retData = retData.split("@")
            retData =list(retData)
            apLists=list()
            
            for items in retData:
                data=str(items).replace("(","").replace(")","").split(",")
                data=tuple(data)
                apLists.append(data)

            return apLists
        else:
            return None
        
    def connectWiFi(self,ssid,pwd):
        """
        Connect to a WiFi AccessPoins
        
        Parameters:
            ssid : WiFi AP's SSID
            pwd : WiFi AP's Password
        
        Retuns:
            WIFI DISCONNECT when failed connect with target AP's credential
            WIFI AP WRONG PASSWORD when tried connect with taget AP with wrong password
            WIFI AP NOT FOUND when cann't find the target AP
            WIFI CONNECTED when successfully connect with the target AP
        """
        txData='AT+CWJAP="{}","{}"\r\n'.format(ssid, pwd)
        #print(txData)
        retData = self._sendToESP(txData)
        #print(".....")
        #print(retData)
        if(retData!=None):
            if "+CWJAP" in retData:
                if "1" in retData:
                    return ESP_WIFI_DISCONNECTED
                elif "2" in retData:
                    return ESP_WIFI_AP_WRONG_PWD
                elif "3" in retData:
                    return ESP_WIFI_AP_NOT_PRESENT
                elif "4" in retData:
                    return ESP_WIFI_DISCONNECTED
                else:
                    return None
            elif ESP_WIFI_CONNECTED in retData:
                if ESP_WIFI_GOT_IP_CONNECTED in retData:
                    return ESP_WIFI_CONNECTED
                else:
                    return ESP_WIFI_DISCONNECTED
            else:
                return ESP_WIFI_DISCONNECTED
        else:
                return ESP_WIFI_DISCONNECTED
            
        
        
    def disconnectWiFi(self):
        """
        Disconnect WIFI
        
        Return:
            False on failed to disconnect the WiFi
            True on successfully disconnected
        """
        retData = self._sendToESP("AT+CWQAP\r\n")
        if(retData!=None):
            if ESP_OK_STATUS in retData:
                return True
            else:
                return False
        else:
            return False

    """
    HTTP operations [GET, POST]
    """
    def _createTCPConnection(self, link, port=80):
        """
        Creates a TCP connection between with the Host.
        Just like create a socket before complete the HTTP Get/Post requests.
        
        Return:
            False on failed to create a socket connection
            True on successfully create and establish a socket connection.
        """
        #self._sendToESP("AT+CIPMUX=0")
        reqProtocol = "TCP"
        if port == 443:
            reqProtocol = "SSL"
        txData='AT+CIPSTART="{}","{}",{}\r\n'.format(reqProtocol, link, str(port))
        #print("txData:", txData)
        retData = self._sendToESP(txData)
        #print(retData)
        if(retData != None):
            if ESP_OK_STATUS in retData:
                return True
            else:
                return False
        else:
            False
    
    def doHttpGet(self,host,path,user_agent="RPi-Pico", port=80, headers=''):
        """
        Do the HTTP GET request
        
        Parameter:
            host (str): Host URL [ex: get operation URL: www.httpbin.org/ip. so, Host URL only "www.httpbin.org"]
            path (str): Get operation's URL path [ex: get operation URL: www.httpbin.org/ip. so, the path "/ip"]
            user-agent (str): User Agent Name [Default "RPi-Pico"]
            port (int): HTTP post number [Default port number 80]
            headers (str): Extra headers, for example Authorization. Remember to add "\r\n" at the end.
        
        Return:
            HTTP error code & HTTP response[If error not equal to 200 then the response is None]
            On failed return 0 and None
        """

        if(self._createTCPConnection(host, port) == True):
            self._createHTTPParseObj()
            getHeader='GET {} HTTP/1.1\r\n{}Host: {}\r\nUser-Agent: {}\r\n\r\n'.format(path, headers, host, user_agent)
            print("Get header: ",getHeader,len(getHeader))
            txData="AT+CIPSEND="+str(len(getHeader))+"\r\n"
            retData = self._sendToESP(txData)
            if(retData != None):
                if ">" in retData:
                    retData = self._sendToESP(getHeader, delay=2)
                    self._sendToESP("AT+CIPCLOSE\r\n")
                    retData=self.__httpResponse.parseHTTP(retData)
                    return retData, self.__httpResponse.getHTTPResponse()
                else:
                    return 0, None
            else:
                return 0, None
        else:
            self._sendToESP("AT+CIPCLOSE\r\n")
            return 0, None
            
        
    def doHttpPost(self,host,path,user_agent,content_type,content,port=80, headers=''):
        """
        Do HTTP POST request
        
        Parameter:
            host (str): Host URL [ex: get operation URL: www.httpbin.org/ip. so, Host URL only "www.httpbin.org"]
            path (str): Get operation's URL path [ex: get operation URL: www.httpbin.org/ip. so, the path "/ip"]
            user-agent (str): User Agent Name [Default "RPi-Pico"]
            content_type (str): Post operation's upload content type [ex. "application/json", "application/x-www-form-urlencoded", "text/plain"
            content (str): Post operation's upload content 
            post (int): HTTP post number [Default port number 80]
            headers (str): Extra headers, for example Authorization. Remember to add "\r\n" at the end.
        
        Return:
            HTTP error code & HTTP response[If error not equal to 200 then the response is None]
            On failed return 0 and None
        
        """
        if(self._createTCPConnection(host, port) == True):
            self._createHTTPParseObj()
            postHeader='POST {} HTTP/1.1\r\n{}Host: {}\r\nUser-Agent: {}\r\nContent-Type: {}\r\nContent-Length: {}\r\n\r\n{}\r\n'.format(path, headers, host, user_agent, content_type, str(len(content)), content)
            txData="AT+CIPSEND="+str(len(postHeader))+"\r\n"
            retData = self._sendToESP(txData)
            if(retData != None):
                if ">" in retData:
                    retData = self._sendToESP(postHeader, delay=2)
                    #print(".......@@",retData)            
                    self._sendToESP("AT+CIPCLOSE\r\n")
                    #print(self.__httpResponse)
                    retData=self.__httpResponse.parseHTTP(retData)
                    return retData, self.__httpResponse.getHTTPResponse()
                else:
                    return 0, None
            else:
                return 0, None
        else:
            self._sendToESP("AT+CIPCLOSE\r\n")
            return 0, None
        
    """
    MQTT operations
    """
    
    def mqttRet(self, retData):
        """
        Return string for most of MQTT methods

        Parameters:
            retData (str): Return data from AT command
        """
        if ESP_OK_STATUS in retData:
            return "OK"
        elif ESP_ERROR_STATUS in retData:
            return "ERROR"
        elif ESP_FAIL_STATUS in retData:
            return "FAIL"
        elif ESP_BUSY_STATUS in retData:
            return "ESP BUSY\r\n"
        else:
            return None

    def setTime(self):
        """
        Setting correct timezone
        """
        txData='AT+CIPSNTPCFG=1,8,"ntp1.aliyun.com","ntp2.aliyun.com"\r\n'
        self._sendToESP(txData)
        txData="AT+CIPSNTPTIME?\r\n"
        retData = self._sendToESP(txData)
        return retData

    def mqttUserConf(self, scheme, clientId, userName, password):
        """
        Setting user configuration
        
        Parameters:
            scheme (int): Connection scheme. As follow:
                1: MQTT over TCP.
                2: MQTT over TLS (no certificate verify).
                3: MQTT over TLS (verify server certificate).
                4: MQTT over TLS (provide client certificate).
                5: MQTT over TLS (verify server certificate and provide client certificate).
                6: MQTT over WebSocket (based on TCP).
                7: MQTT over WebSocket Secure (based on TLS, no certificate verify).
                8: MQTT over WebSocket Secure (based on TLS, verify server certificate).
                9: MQTT over WebSocket Secure (based on TLS, provide client certificate).
                10: MQTT over WebSocket Secure (based on TLS, verify server certificate and provide client certificate).
            clientId (str): MQTT client ID. Maximum length: 256 bytes.
            userName (str): The username to login to the MQTT broker. Maximum length: 64 bytes.
            password (str): the password to login to the MQTT broker. Maximum length: 64 bytes.

        Return:
            mqttRet string
        """
        txData='AT+MQTTUSERCFG=0,{},"{}","{}","{}",0,0,""\r\n'.format(scheme, clientId, userName, password)
        retData = self._sendToESP(txData)
        return self.mqttRet(retData)
        
    def mqttConnectionConf(self, host, port, reconnect=1):
        """
        Configure connection

        Parameters:
            host (str): MQTT broker domain. Maximum length: 128 bytes.
            port (int): MQTT broker port. Maximum: port 65535.
            reconnect (int): Following values:
                0: MQTT will not reconnect automatically.
                1: MQTT will reconnect automatically. It takes more resources.

        Return:
            mqttRet string
        """
        txData='AT+MQTTCONN=0,"{}",{},{}\r\n'.format(host,str(port),str(reconnect))
        retData = self._sendToESP(txData)
        return self.mqttRet(retData)
        
    def mqttPublish(self, topic, data, qos=1, retain=0):
        """
        Publish message to MQTT server

        Parameters:
            topic (str): MQTT topic. Maximum length: 128 bytes.
            data (str): MQTT message in string.
            qos (int): QoS of message, which can be set to 0, 1, or 2. Default: 0.
            retain (int): retain flag.

        Return:
            mqttRet string
        """
        txData='AT+MQTTPUB=0,"{}","{}",{},{}\r\n'.format(topic, data, str(qos), str(retain))
        retData = self.mqttRet(self._sendToESP(txData))
        
    def mqttSubscribe(self, topic, qos=1):
        """
        Subscribe to MQTT topic

        Parameters:
            topic (str): MQTT topic. Maximum length: 128 bytes.
            qos (int): QoS of message, which can be set to 0, 1, or 2. Default: 0.

        Return:
            
        """
        txData='AT+MQTTSUB=0,"{}",{}\r\n'.format(topic, str(qos))
        retData = self._sendToESP(txData)

    def mqttClose(self):
        """
        Close MQTT connection
        """
        retData = self.mqttRet(self._sendToESP("AT+MQTTCLEAN=0"))

    def listenForIncome(self, delay=None):
        """
        Listen for incoming data

        Parameters:
            delay (float): Delay between scans

        Return: 
            List containing: MQTT res type, Topic, length, Message
        """
        self.__rxData=str()
        self.__rxData=bytes()
        
        time.sleep(delay)
        
        while True:
            #print(".")
            if self.__uartObj.any()>0:
                #print(self.__uartObj.any())
                break
        
        while self.__uartObj.any()>0:
            self.__rxData += self.__uartObj.read(UART_Rx_BUFFER_LENGTH)
        
        res = self.__rxData.decode('utf-8')
        res = res.replace('\r\n', '')
        res = res.split(',')
        return res
        
        
    def __del__(self):
        """
        The distaructor for ESP8266 class
        """
        print('Destructor called, ESP8266 deleted.')
        pass

