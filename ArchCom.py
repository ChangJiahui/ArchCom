# -*- coding: utf-8 -*-
"""
Created on Thu Jul  5 17:09:25 2018

@author: CHANG
"""

from pyaudio import PyAudio, paInt16
import numpy as np
import wave
from aip import AipSpeech
import threading

import requests
import urllib.request
import json
from json import JSONDecoder

import serial.tools.list_ports
from pythonosc import dispatcher, osc_server

import time
import cv2
import os
import random

SPEAK_PER = 0
PEOPLE_NUM = 0
HAPPYNESS = 0
CHAIR_OPEN = False
BI_HEART = False
EMOTION = ""

LDATA = False

FILELCK = threading.Lock()
AUDIOLCK = threading.Lock()
RECORDLCK = threading.Lock()

ISPLAY = False


def audioplay(filepath):
    # define stream chunk
    chunk = 1024
    # wav 文件读取
    fp = wave.open(filepath, 'rb')
    params = fp.getparams()
    nchannels, sampwidth, framerate, nframes = params[:4]
    # instantiate PyAudio
    pa = PyAudio()
    # 打开声音输出流
    stream = pa.open(format=pa.get_format_from_width(sampwidth), channels=nchannels, rate=framerate, output=True)
    # 写声音输出流到声卡进行播放
    data = fp.readframes(chunk)
    while True:
        data = fp.readframes(chunk)
        if data==b'': break
        stream.write(data)
    fp.close()
    stream.stop_stream()
    stream.close()
    pa.terminate()


class faceplusplus:
    KEY = "kCHIkXOkh2vLM-ElrMZx3_7teqjp40-O"
    SECRET = "zIMcdjKxxBbN2JTnwEnpcuvAbgzQdlIJ" 


    def gesturerec(self, filepath):
        gesture_url = "https://api-cn.faceplusplus.com/humanbodypp/beta/gesture"
        data = {"api_key":self.KEY, "api_secret": self.SECRET, "return_gesture": "1"} 
        files = {"image_file": open(filepath, 'rb')}
        response = requests.post(gesture_url, data=data, files=files)
        req_con = response.content.decode('utf-8')
        req_dict = JSONDecoder().decode(req_con)
        #    print(req_dict)
        return req_dict

    def facecompare(self, filepath, filepath2):
        facecompare_url = "https://api-cn.faceplusplus.com/facepp/v3/compare"
        data = {"api_key":self.KEY, "api_secret": self.SECRET} 
        files = {"image_file1": open(filepath, 'rb'), "image_file2": open(filepath2, "rb")}
        response = requests.post(facecompare_url, data=data, files=files)
        req_con = response.content.decode('utf-8')
        req_dict = JSONDecoder().decode(req_con)
        return req_dict

    def facedetect(self, filepath):
        facedetect_url = "https://api-cn.faceplusplus.com/facepp/v3/detect"
        data = {"api_key":self.KEY, "api_secret": self.SECRET, "return_attributes": "gender,age,emotion,beauty,smiling"} 
        files = {"image_file": open(filepath, 'rb')}
        response = requests.post(facedetect_url, data=data, files=files)
        req_con = response.content.decode('utf-8')
#        print(req_con)
        req_dict = JSONDecoder().decode(req_con)
        return req_dict




class recoder:
    # Can be modified
    LEVEL = 2000             # 音量保存的阈值
    SILENCE_TIME = 1        # 录音1s安静则结束录音
    MAX_TIME = 100           # 录音时间，单位 s

    # Better be fixed
    NUM_SAMPLES = 2000      # pyaudio 内置缓冲大小
    SAMPLING_RATE = 16000   # 取样频率
    COUNT_NUM = 30         # NUM_SAMPLING个取样之内出现COUNT_NUM个大于LEVEL的取样则记录声音
    SILENCE_TIME_COUNT = SILENCE_TIME * SAMPLING_RATE / NUM_SAMPLES
    MAX_TIME_COUNT = MAX_TIME * SAMPLING_RATE / NUM_SAMPLES
    CHANNELS = 1
    SAMPWIDTH = 2
    FORMAT = paInt16

    Voice_String = []

    def savewav(self, filename):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.SAMPWIDTH)
        wf.setframerate(self.SAMPLING_RATE)
        wf.writeframes(np.array(self.Voice_String).tostring())
        # wf.writeframes(self.Voice_String.decode())
        wf.close()

    def recoder(self):
        global ISPLAY

        pa = PyAudio()
        stream = pa.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.SAMPLING_RATE, input=True, frames_per_buffer=self.NUM_SAMPLES)
        save_count = 0
        save_buffer = []
        time_count = 0
        silent_count = 0
        Voice_String = []
        string_audio_data = stream.read(self.NUM_SAMPLES)

        while True:
            save_buffer.append(string_audio_data)
            # 读入NUM_SAMPLES个取样
            string_audio_data = stream.read(self.NUM_SAMPLES)
            # 将读入的数据转换为数组
            audio_data = np.fromstring(string_audio_data, dtype=np.short)
            # 计算大于LEVEL的取样的个数
            np.where(audio_data>500, audio_data, 0)
            large_sample_count = np.sum(audio_data>self.LEVEL)
            if(ISPLAY):
                stream.stop_stream()
                stream.close()
                pa.terminate()
                return
            print(np.max(audio_data))
            # 如果个数大于COUNT_NUM,则至少保存 SAVE_LENTH 个块
            if (large_sample_count > self.COUNT_NUM):
                    silent_count = 0
                    print("start recoding!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    while True:
                        if(ISPLAY):
                            stream.stop_stream()
                            stream.close()
                            pa.terminate()
                            return
                        save_buffer.append(string_audio_data)
                        time_count+=1
                        # 读入NUM_SAMPLES个取样
                        string_audio_data = stream.read(self.NUM_SAMPLES)
                        # 将读入的数据转换为数组
                        audio_data = np.fromstring(string_audio_data, dtype=np.short)
                        # 计算大于LEVEL的取样的个数
                        large_sample_count = np.sum(audio_data>self.LEVEL)
                        print(np.max(audio_data))
                        if(large_sample_count < self.COUNT_NUM):
                            silent_count += 1
                        else:
                            silent_count =0

                        if((silent_count>=self.SILENCE_TIME_COUNT) or (time_count>=self.MAX_TIME_COUNT)):
                            self.Voice_String = save_buffer
                            save_buffer = []
                            print('Recode a piece of voice successfully!')
                            stream.stop_stream()
                            stream.close()
                            pa.terminate()
                            return True
            else:
                save_buffer = []
    def record(self, filename):
        self.recoder()
        self.savewav(filename)


class baiduaudio:
    APP_ID = '11485920'
    API_KEY = 'eoP5OSsfedXTjQ4IDkaBWO2Q'
    SECRET_KEY = 'L1T5c4v3GOzIvsmdfuurvSyfaj1Se5qB'

    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

    # 读取文件
    def get_file_content(self, filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()

    def baiduasr(self, filePath):
#       fileformat = filePath[(filePath.find('.')+1):]
        return self.client.asr(self.get_file_content(filePath), 'wav', 16000, {'dev_pid': 1536,})

    def baidusynthesis(self, tex, filePath, spd=5, pit=5, vol=10, per=0, lan='zh'):
        result = self.client.synthesis(tex, lan, 1, {'vol': vol,'spd': spd, 'pit': pit, 'per': per,})
        if not isinstance(result, dict):
            with open(filePath, 'wb') as fp:
                fp.write(result)
        return True
    def baidusay(self, tex, filePath, spd=5, pit=5, vol=5, per=0, lan='zh'):
        print(tex)
        print("\n\n\n")
        while(len(tex)>60):
            spktex = tex[:60]
            print(spktex)
            if(spktex.rfind("。\”")!=-1):
                spktex = spktex[:(spktex.rfind("。\”")+len("。\”"))]
            elif(spktex.rfind("。")!=-1):
                spktex = spktex[:(spktex.rfind("。")+1)]
            elif(spktex.rfind("，")!=-1):
                spktex = spktex[:(spktex.rfind("，")+1)]
            elif(spktex.rfind(",")!=-1):
                spktex = spktex[:(spktex.rfind(",")+1)]
            self.baidusynthesis(spktex, filePath, spd=5, pit=5, vol=5, per=per, lan='zh')
            os.system('ffmpeg -i ' + filePath + ' ' + filePath + ' -y')
            audioplay(filePath)
            tex = tex[len(spktex):]
        self.baidusynthesis(tex, filePath, spd=5, pit=5, vol=5, per=per, lan='zh')
        os.system('ffmpeg -i ' + filePath + ' ' + filePath + ' -y')
        audioplay(filePath)

        return True



def tulingrobot(text):
    api_url = "http://openapi.tuling123.com/openapi/api/v2"
    req = {
        "reqType":0,
        "perception":{
            "inputText":{
                "text": text
            },
            "selfInfo":{
                "location":{
                    "city": "北京",
                    "province": "北京",
                    "street": "清华东路"
                }
            }
        },
        "userInfo": 
        {
            "apiKey": "660ded971ec5471aa413eba92c1c7c83",
            "userId": "keywater"
        }
    }
    # print(req)
    # 将字典格式的req编码为 utf-8
    req = json.dumps(req).encode('utf8')
    # print(req)

    http_post = urllib.request.Request(api_url, data=req, headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(http_post)
    response_str = response.read().decode('utf8')
#    print(response_str)
    response_dic = json.loads(response_str)
#    print(response_dic)

    intent_code = response_dic['intent']['code']
    results_text = response_dic['results'][0]['values']['text']
    return results_text


def text_save(content, filename, mode='w'):
    with open(filename, mode) as fp:
        for ii in range(len(content)):
            fp.write(str(content[ii])+'\n')
        return True
    return False

def text_read(filename):
    with open(filename, 'r', encoding='utf-8') as fp:
        content = fp.readlines()
        for ii in range(len(content)):
            content[ii] = content[ii][:-1]
        return content
    return []


def audiocom():
    global AUDIOLCK
    global RECORDLCK
    global ISPLAY

    global SPEAK_PER

    dereply = ["我还小哦，你说话要慢一点，大声一点我才听得懂哦", "周围好吵呀，都听不到你在说什么了", "咦？是你在说话吗", "你说的太快了啦", "我还小，听不清你在说什么", "你刚才说什么？我没听到", "你可以再说一遍吗?", "嘿，你看那有飞船!", "我是不是很笨，为什么听不懂你说的话呀", "世界上最遥远的距离，就是你站在我面前，而我却不知道你在说什么", "不好意思，我刚才走神了，你在说什么?"]
    singreply = ["那你可听好了，我要开始唱了", "我可是个麦霸哦,我唱起来可停不下咯", "你自己打开手机听不就好了,当然了，它没有我唱的好听哦"]
    re = recoder()
    ba = baiduaudio()
    while True:
        if((not ISPLAY) and RECORDLCK.acquire(True)):
            re.record('./voicecache/dialisten.wav')
            RECORDLCK.release()
        if(ISPLAY):
            continue
        asrresult = ba.baiduasr('./voicecache/dialisten.wav')
        print(asrresult)
        if("__json_decode_error" in asrresult.keys()):
            continue
        code = asrresult['err_no']
        if((not ISPLAY) and AUDIOLCK.acquire(True)):
            ISPLAY = True
            listenresult = ""
            spkresult = ""
            if(code==0):
                listenresult = asrresult['result'][0]
                if(("唱" in listenresult) and ("歌" in listenresult)):
                    spkresult = random.choice(singreply)
                    ba.baidusay(spkresult, './voicecache/diaspeak.wav', per=SPEAK_PER)
                    audioplay('./music/' + str(random.randint(1,31)) + '.wav')
                else:
                    spkresult = tulingrobot(listenresult)
                    ba.baidusay(spkresult, './voicecache/diaspeak.wav', per=SPEAK_PER)
            else:
                spkresult = random.choice(dereply)
                ba.baidusay(spkresult, './voicecache/diaspeak.wav', per=SPEAK_PER)
            with open("./data/spklog.txt", 'a') as fp:
                fp.write(time.strftime('%Y-%m-%d %X', time.localtime()) + ",listen," + listenresult + "\n")
                fp.write(time.strftime('%Y-%m-%d %X', time.localtime()) + ",speak," + spkresult + "\n")
            time.sleep(1)
            ISPLAY = False
            AUDIOLCK.release()

def facecom(No):
    global AUDIOLCK
    global RECORDLCK
    global ISPLAY

    global PEOPLE_NUM
    global HAPPYNESS
    global BI_HEART
    global EMOTION
    global SPEAK_PER

    fa = faceplusplus()
    re = recoder()
    ba = baiduaudio()
    name_list = text_read('./facedata/name_list.txt')
    cappath = "./photocache/capture" + str(int(No)) + ".jpg"
    facedatapath = "./facedata/"

    personTimer = 0
    xpos = 0
    ypos = 0

    while True:
        BI_HEART = False
#        caprb = open(cappath, 'rb')
        if(FILELCK.acquire(True)):
            os.system("cp ./photocache/capture.jpg " + cappath)
            FILELCK.release()
        face_req = fa.facedetect(cappath)
        with open("./data/facerequest1.txt", 'a') as fp:
            fp.write(time.strftime('%Y-%m-%d %X', time.localtime()) + "," + str(face_req) + "\n")
        print("\n\n\n")
        print(face_req)
        if("error_message" in face_req.keys()):
            continue
        PEOPLE_NUM = len(face_req['faces'])
        if(PEOPLE_NUM>0):
            if(face_req['faces'][0]['attributes']['gender']['value']=="Male"):
                SPEAK_PER = 0
            else:
                SPEAK_PER = 1
#            print("smile : " + str(face_req['faces'][0]['attributes']['smile']['value']))
            happy_sum = 0
            for ii in range(PEOPLE_NUM):
                happy_sum = happy_sum + face_req['faces'][ii]['attributes']['smile']['value']
            HAPPYNESS = happy_sum/PEOPLE_NUM
#            print("age : " + str(face_req['faces'][0]['attributes']['age']['value']))
#            print("emotion : " + str(face_req['faces'][0]['attributes']['emotion']))
#            print("beauty : " + str(face_req['faces'][0]['attributes']['beauty']))
            emotiondict = face_req['faces'][0]['attributes']['emotion']
            EMOTION = max(emotiondict, key = emotiondict.get)
            print(EMOTION)
            gesture_req = fa.gesturerec(cappath)
            with open("./data/gesturerequest.txt", 'a') as fp:
                fp.write(time.strftime('%Y-%m-%d %X', time.localtime()) + "," + str(gesture_req) + "\n")
            if ((not ISPLAY) and ('hands' in gesture_req.keys())):
                if(len(gesture_req['hands'])>0):
                    if(AUDIOLCK.acquire(True)):
                        ISPLAY = True
                        newface = False
#                        BI_HEART = False
                        BI_HEART = True
                        for ii in range(len(gesture_req['hands'])):
                            gesturedict = gesture_req['hands'][ii]['gesture']
                            gesture = max(gesturedict, key=gesturedict.get)
                            max_prop = gesturedict[gesture]
                            print(gesture, max_prop)
#                            if((("heart" in gesture) or "thumb_up" in gesture) and (max_prop>50)):
                            if("heart" in gesture):
                                BI_HEART = True
                                break
                        if(BI_HEART):
                            ba.baidusay("你好面熟呀，我们是不是在哪里见过呢?让我想想哈", './voicecache/facecompare.wav', per=SPEAK_PER)
                            newface = True
                            for ii in range(len(name_list)):
                                facepath = facedatapath+str(ii)+'.jpg'
                                facecomrec = fa.facecompare(cappath, facepath)
                                print(facecomrec)
                                if(facecomrec["confidence"]>80):
                                    print((name_list[ii] + "您好呀"))
                                    ba.baidusay(("啊，我想起来了，" + name_list[ii] + "您好呀"), './voicecache/oldname.wav', per=SPEAK_PER)
                                    newface = False
                                    break
                        if(newface):
                            ba.baidusay("原来是新朋友呀，请问您的名字叫什么呢？", './voicecache/newface.wav', per=SPEAK_PER)
                            if(RECORDLCK.acquire(True)):
                                ISPLAY = False
                                re.record('./voicecache/namelisten.wav')
                                ISPLAY = True
                                RECORDLCK.release()
                            asrresult = ba.baiduasr('./voicecache/namelisten.wav')
                            print(asrresult)
                            code = asrresult['err_no']
                            if(code==0):
                                listenresult = asrresult['result'][0]
                                if(listenresult==""):
                                    ba.baidusay("我没听清您的名字，可以再向我比颗小心心吗", './voicecache/namenoise', per=SPEAK_PER)
                                    time.sleep(1)
                                    ISPLAY = False
                                    AUDIOLCK.release()
                                    continue
                                # 需要试一下人们报名字的方式
                                if("是" in listenresult):
                                    listenresult = listenresult[listenresult.index("是"):]
                                if("叫" in listenresult):
                                    listenresult = listenresult[listenresult.index("叫"):]
                                facepath = facedatapath+str(len(name_list))+'.jpg'
                                name_list.append(listenresult)
                                text_save(name_list, './name_list.txt')
                                os.system("cp " + cappath + " " + facepath)
                                ba.baidusay((listenresult + "您好，我是全宇宙最贴心的 Fancy Hub 哦，我能读懂你的每一个表情，很高兴认识你哦。"), './voicecache/newname.wav', per=SPEAK_PER)
                        time.sleep(1)
                        ISPLAY = False
                        AUDIOLCK.release()
        else:
            personTimer=0
            HAPPYNESS = 0
#        cv2.waitKey(10)

def facetimecount():
    global FILELCK
    global AUDIOLCK

    global CHAIR_OPEN
    global ISPLAY

    fa = faceplusplus()
    re = recoder()
    ba = baiduaudio()
    
    personTimer = 0
    xpos = 0
    ypos = 0
    cappath = "./photocache/facetimecount.jpg"


    while True:
        if(FILELCK.acquire(True)):
            os.system("cp ./photocache/capture.jpg " + cappath )
            FILELCK.release()
        face_req = fa.facedetect(cappath)
        with open("./data/facerequest2.txt", 'a') as fp:
            fp.write(time.strftime('%Y-%m-%d %X', time.localtime()) + "," + str(face_req) + "\n")
        if("error_message" in face_req.keys()):
            continue
        if(len(face_req['faces'])>0):
            face_rect = face_req['faces'][0]['face_rectangle']
            xpos_temp = face_rect['left'] + face_rect['width']/2
            ypos_temp = face_rect['top'] + face_rect['height']/2
            print("xpos:" + str(xpos_temp))
            print("ypos:" + str(ypos_temp))
            if(personTimer==0):
                personTimer = 1
                xpos = xpos_temp
                ypos = ypos_temp
            else:
                if((abs(xpos-xpos_temp)<50) and abs(ypos-ypos_temp)<50):
                    personTimer = personTimer + 1
                    if(personTimer>10):
                        if(AUDIOLCK.acquire(True)):
                            ISPLAY = True
                            ba.baidusay("你在这里呆了很久，要不要坐下来休息一会儿呀",'./voicecache/rest.wav',per=SPEAK_PER)
                            time.sleep(1)
                            ISPLAY = False
                            AUDIOLCK.release()
                        print("CHAIR ON!!!")
                        CHAIR_OPEN = True
                        personTimer = 0
                else:
                    personTimer = 0
        else:
            xpos = 0
            ypos = 0
        time.sleep(1)


def C_Serial():
    serialFd = serial.Serial("/dev/ttyACM0", 115200, timeout=60)

    while(True):
        global PEOPLE_NUM
        global HAPPYNESS
        global CHAIR_OPEN
        global BI_HEART
        global EMOTION


        PN = 0
        HN = 0
        CO = 0
        BH = 0
        ET = 0

#        serialFd.flush()
#        serialFd.flushOutput()
#        time.sleep(0.1)
        

        if(not serialFd.isOpen()):
            serialFd.open()
            
        if(PEOPLE_NUM>6):
            PN=6
        else:
            PN=PEOPLE_NUM

        if(HAPPYNESS<12.5):
            HN=1
        elif((HAPPYNESS<25) and (HAPPYNESS>12.5)):
            HN=2
        elif((HAPPYNESS<37.5) and (HAPPYNESS>25)):
            HN=3
        elif((HAPPYNESS<50) and (HAPPYNESS>37.5)):
            HN=4
        elif((HAPPYNESS<62.5) and (HAPPYNESS>50)):
            HN=5
        elif((HAPPYNESS<75) and (HAPPYNESS>62.5)):
            HN=6
        elif((HAPPYNESS<87.5) and (HAPPYNESS>75)):
            HN=7
        elif((HAPPYNESS<100) and (HAPPYNESS>87.5)):
            HN=8

        if(CHAIR_OPEN):
            CO=1

        if(BI_HEART):
            BH=1
    
        str_temp = "A"+str(int(BH))+","+str(int(PN))+","+str(int(HN))+","+str(int(CO))+"\n"
        print("C_Serial:" + str_temp)
        serialFd.write(str_temp.encode('utf-8'))
        serialFd.flush()
        time.sleep(0.1)


        if(CO==1):
            for ii in range(50):
                if(PEOPLE_NUM>6):
                    PN=6
                else:
                    PN=PEOPLE_NUM
                if(HAPPYNESS<12.5):
                    HN=1
                elif((HAPPYNESS<25) and (HAPPYNESS>12.5)):
                    HN=2
                elif((HAPPYNESS<37.5) and (HAPPYNESS>25)):
                    HN=3
                elif((HAPPYNESS<50) and (HAPPYNESS>37.5)):
                    HN=4
                elif((HAPPYNESS<62.5) and (HAPPYNESS>50)):
                    HN=5
                elif((HAPPYNESS<75) and (HAPPYNESS>62.5)):
                    HN=6
                elif((HAPPYNESS<87.5) and (HAPPYNESS>75)):
                    HN=7
                elif((HAPPYNESS<100) and (HAPPYNESS>87.5)):
                    HN=8
                if(CHAIR_OPEN):
                    CO=1
                str_temp = "A"+str(int(BH))+","+str(int(PN))+","+str(int(HN))+","+str(int(CO))+"\n"
                print("C_Serial:" + str_temp)
                serialFd.write(str_temp.encode('utf-8'))
#                time.sleep(0.1)
                serialFd.flush()
#                serialFd.flushOutput()
                time.sleep(0.1)

        if(BH==1):
            for ii in range(50):
                if(PEOPLE_NUM>6):
                    PN=6
                else:
                    PN=PEOPLE_NUM
                if(HAPPYNESS<12.5):
                    HN=1
                elif((HAPPYNESS<25) and (HAPPYNESS>12.5)):
                    HN=2
                elif((HAPPYNESS<37.5) and (HAPPYNESS>25)):
                    HN=3
                elif((HAPPYNESS<50) and (HAPPYNESS>37.5)):
                    HN=4
                elif((HAPPYNESS<62.5) and (HAPPYNESS>50)):
                    HN=5
                elif((HAPPYNESS<75) and (HAPPYNESS>62.5)):
                    HN=6
                elif((HAPPYNESS<87.5) and (HAPPYNESS>75)):
                    HN=7
                elif((HAPPYNESS<100) and (HAPPYNESS>87.5)):
                    HN=8
                if(CHAIR_OPEN):
                    CO=1
                str_temp = "A"+str(int(BH))+","+str(int(PN))+","+str(int(HN))+","+str(int(CO))+"\n"
                print("C_Serial:" + str_temp)
                serialFd.write(str_temp.encode('utf-8'))
#                time.sleep(0.1)
                serialFd.flush()
#                serialFd.flushOutput()
                time.sleep(0.1)
            BI_HEART = False
        serialFd.close()


def Roof_Serial():
    global LDATA
    global PEOPLE_NUM

    serialFd = serial.Serial(port="/dev/ttyACM1", baudrate=115200, timeout=60)

    while(True):
        serialFd.flush()
        serialFd.flushOutput()
        time.sleep(0.1)
        if(not serialFd.isOpen()):
            serialFd.open()
        PN = 1
        if(PEOPLE_NUM>0):
            PN = 2
        if(LDATA):
            str_temp = "R3\n"
            for ii in range(10):
#                serialFd.flushOutput()
                serialFd.write(str_temp.encode('utf-8'))
                time.sleep(0.1)
        else:
            str_temp = "R" + str(int(PN)) + "\n"
#            serialFd.flushOutput()
            serialFd.write(str_temp.encode('utf-8'))
            time.sleep(0.1)
#        print("R_Serial:" + str_temp)


#        EM = 0
#        if(EMOTION == "happiness"):
#            EM = 1
#        elif(EMOTION == "surprise"):
#            EM = 2
#        elif(EMOTION == "fear"):
#            EM = 3
#        elif(EMOTION == "neutral"):
#            EM = 4
#        elif(EMOTION == "sadness"):
#            EM = 5
#        elif(EMOTION == "disgust"):
#            EM = 6
#        elif(EMOTION == "anger"):
#            EM = 7

#        if((LRED>0) and (LGREEN>0) and (LBLUE>0)):
#            for ii in range(50):
#
#                str_temp = "R"+str(int(EM))+","+str(int(LRED))+","+str(int(LGREEN))+"."+str(int(LBLUE))+"\n"
#                print("R_serial:"+str_temp)
#                serialFd.write(str_temp.encode('utf-8'))
#                time.sleep(0.1)
#            LRED=0
#            LGREEN=0
#            LBLUE=0
#        else:
#            str_temp = "R"+str(int(EM))+","+"0,0,0\n"
#            print("R_serial:"+str_temp)
#            serialFd.write(str_temp.encode('utf-8'))
#            time.sleep(0.1)

def osc_Ldata(unused_address, str_temp):
    global LDATA
    if(str_temp == "1"):
        LDATA = True
    else:
        LDATA = False

def oscserver():
    osc_disp = dispatcher.Dispatcher()
#    osc_disp.map(".*", osc_handler)
    osc_disp.map(".*", osc_Ldata)
    server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", 8888), osc_disp)
    server.serve_forever()

def cv2Video():
    global FILELCK

    cap = cv2.VideoCapture(0)
    cappath = "./photocache/capture.jpg"
    while True:
        ret, frame = cap.read()
#        cv2.imshow("capture", frame)
        if(FILELCK.acquire(True)):
            cv2.imwrite(cappath, frame)
            FILELCK.release()
        cv2.waitKey(1)

def COCOUNT():
    global AUDIOLCK

    global CHAIR_OPEN

    ba = baiduaudio()
    while True:
        if(CHAIR_OPEN):
            time.sleep(30)
            if(AUDIOLCK.acquire(True)):
                ba.baidusay("休息的差不多了，快起来运动运动吧",'./voicecache/chair.wav')
                time.sleep(1)
                AUDIOLCK.release()
            CHAIR_OPEN = False

def fileout():
    global SPEAK_PER
    global PEOPLE_NUM
    global HAPPYNESS
    global CHAIR_OPEN
    global BI_HEART
    global EMOTION

    while True:
        with open("./data/data.txt",'a') as fp:
            fp.write(time.strftime('%Y-%m-%d %X', time.localtime()) + "," + str(SPEAK_PER) + "," + str(PEOPLE_NUM) + "," + str(HAPPYNESS) +"\n")

threads = []

t0 = threading.Thread(target=cv2Video)
threads.append(t0)
t1 = threading.Thread(target=audiocom)
threads.append(t1)
#t2_1 = threading.Thread(target=facecom, args=(1,))
#threads.append(t2_1)
#t3 = threading.Thread(target=facetimecount)
#threads.append(t3)

#t4 = threading.Thread(target=oscserver)
#threads.append(t4)
#t5 = threading.Thread(target=Roof_Serial)
#threads.append(t5)
#t6 = threading.Thread(target=C_Serial)
#threads.append(t6)
#t7 = threading.Thread(target=COCOUNT)
#threads.append(t7)
#t8 = threading.Thread(target=fileout)
#threads.append(t8)


if __name__ == '__main__':
    for t in threads:
        t.setDaemon(False)
        t.start()
