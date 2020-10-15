# encoding: utf-8
import os, sys
from pathlib import Path
import subprocess
import requests
from urllib import request
from bs4 import BeautifulSoup
import bs4
import re
###ini文件读取模块
import configparser
from datetime import datetime
import threading
import time
from threading import Timer
import runScript
from Logger import Logger
import globalVar as gl
# 全局变量#
##脚本遍历的间隔
INTERVAL_VAR = 60*5
##获取目标的url地址
REQUEST_URL =  'http://192.168.103.123/download/'
##当天的日期
LOCAL_DATE =  ''
##本地存储zip包和apk的绝对路径地址
LOCAL_DIR = ''
ROOT_DIR = '/home/yunce/airtest-auto/static/'
DEVICE_LIST = ['E6E4C20420026353','66B0220226000709', 'MDX0220814027217']
DEVICE_MODEL_LIST =  ['JEF-AN00','OXF-AN10','ELS-AN00']
##庆余年游戏的压缩包文件夹
QYN_STATIC_PATH = 'Android_Hpf'
log = Logger(filename='/home/yunce/airtest-auto/log/all.log',level='debug')
Logger('/home/yunce/airtest-auto/log/error.log', level='error').logger.error('error')


def getApkDownloadUrl(versionNum):
 ###获取ini文件读取路径
    rIni = requests.get(REQUEST_URL + LOCAL_DATE + '/airtest_config_' + versionNum +'.ini')
    if rIni.status_code == 200:
        log.logger.error('INIfile get success')
        INIcontent = rIni.content.decode("utf-8")
        #去空格&回车换行进行切割
        INIlist = INIcontent.replace(" ", "").split('\r\n')
        INIreversion = INIlist[1].split("=")[1]
        INIapkname = INIlist[3].split("=")[1]
        INIzipname = INIlist[4].split("=")[1]
        INIpackagename = INIlist[5].split("=")[1]
        INIrooturl = INIlist[6].split("=")[1]
        _apkInfo= {
            'reversion': INIreversion,
            'apkname': INIapkname,
            'zipname': INIzipname,
            'packagename': INIpackagename,
            'rooturl': INIrooturl
            }
        return _apkInfo
    else:
        log.logger.error('INIfile get error')
#验证待下载的文件
def vailDownloadFile(_url):
    try:
        rDownload = request.urlopen(_url)
    except:
        log.logger.error('下载地址:%s 不存在,抛出异常' % _url)    
    else:
        if rDownload.status == 200:
            log.logger.info('下载地址:%s 存在' % _url)    
            return True


#下载文件
def downloadFile(url,file_name,reversion):
    ##验证待下载的文件是否已经存在
    _localFile = Path(LOCAL_DIR + file_name)
    if _localFile.exists():
        log.logger.info('%s is already exist' % file_name)
    else :    
        ##待下载的文件是否存在
        _fileState = vailDownloadFile(url)
        if _fileState == True:
            log.logger.info('start download %s' % file_name)
            subprocess.call('wget -c -O ' + LOCAL_DIR  + file_name + ' ' + url, shell=True)
            ##zip包验证格式并解压
            zipFileType = file_name.split('.')[1]
            if zipFileType == 'zip':
                ##创建存放解压文件的文件夹
                inner_dir_path = LOCAL_DIR + reversion + '/'
                os.mkdir(inner_dir_path)
                subprocess.call('unzip ' + str(_localFile) + ' -d ' + inner_dir_path, shell=True)
                log.logger.info('%s unzip success' % file_name)
            
##遍历设备列表 查询是否有新任务需要执行
def checkScriptState(localApkInfo):
    ##定义线程池
    #threadList = []
    names = locals()
    for i,j in enumerate(DEVICE_LIST):
        ##检查当前设备是否正在执行任务
        ##以静态文件是否存在判断
        _scriptRunState = Path(ROOT_DIR + j + '/' + j + '.txt')
        if _scriptRunState.exists():
            log.logger.info('deivce: %s still running script' % j)
        else :
            taskApkPath= LOCAL_DIR + localApkInfo['apkname']
            taskFilesPath= LOCAL_DIR + localApkInfo['reversion'] + '/' + QYN_STATIC_PATH + '/*'
            taskPackageName= localApkInfo['packagename']
            taskVersion= localApkInfo['reversion']
            taskModelName = DEVICE_MODEL_LIST[i]
            log.logger.debug(taskApkPath)
            log.logger.debug(taskFilesPath)
            log.logger.debug(taskPackageName)
            log.logger.debug(taskVersion)
            timeCounter = 0
            while True:
                _counter = gl.get_value('counter')
                if(_counter < 1 or timeCounter > 9):
                    ##调用runscript的执行脚本
                    # names['n' + str(j) ] = threading.Thread(target=runScript.insertApk,args=(j,taskApkPath))
                    # names['n' + str(j) ].start()
                    names['n' + str(j) ] = threading.Thread(target=runScript.init,args=(j,taskApkPath,taskFilesPath,taskPackageName,taskVersion,taskModelName,log))
                    names['n' + str(j) ].start()
                    ##修改计数器的值
                    _counter = _counter + 1
                    gl.set_value('counter', _counter)
                    log.logger.info('counter值为%s' % _counter)
                    #runScript.init(i,taskApkPath,taskFilesPath,taskPackageName,taskVersion)
                    log.logger.info('deivce: %s prepare install apk and push files' % j)
                    # time.sleep(5)
                    break
                else:
                    time.sleep(60)
                    ##while遍历次数的计数器，大于10分钟则开始下一个设备的安装
                    timeCounter = timeCounter + 1
                    log.logger.info('timeCounter times: %s' % timeCounter)
                    log.logger.info('waiting for deivce: %s install apk' % j)

##验证当前设备的apk版本信息
# def valiApkVersion(serial,packageName):
#     p = subprocess.Popen('adb -s ' + serial  + 'shell dumpsys package ' + packageName + ' | grep versionName', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
#     output, err = p.communicate()
#     # 判断命令是否执行成功
#     status = 1 if err else 0
#     if status == 0:
#         print('[SUCCESS]adb -s %s shell dumpsys package %s | grep versionName' %(serial, packageName))
#         output = output.decode("utf-8").replace(" ", "").split('=')
#         print('[INFO]device %s package %s version is %s' %(serial, packageName, output[1]))
#     else:
#         print('[ERROR]adb -s %s shell dumpsys package %s | grep versionName' %(serial, packageName))
#         print(err)
#     return status, output


###将adb和python进程全部重启
# def restartProcess():
#     subprocess.call('adb kill-server', shell=True)
#     time.sleep(0.5)
#     subprocess.call('adb start-server', shell=True)
#     time.sleep(10)

# def counterTxtCreate(num):
#     full_path = '/home/yunce/airtest-auto/counter.txt'  # 也可以创建一个.doc的word文档
#     file = open(full_path, 'w+')
#     file.write(num)
#     log.logger.debug("当前counter值为%s" %num)
#     file.close()


# def counterTxtModify():
#     full_path = '/home/yunce/airtest-auto/counter.txt'  # 也可以创建一个.doc的word文档
#     file = open(full_path, 'r+')
#     _num = file.read()
#     _num = int(_num) + 1
#     log.logger.debug("当前counter值为%s" %_num)
#     file.close()

#     file1 = open(full_path, 'w+')
#     file1.write(str(_num))
#     file1.close()

def counterTxtRead():
    full_path = '/home/yunce/airtest-auto/counter.txt'  # 也可以创建一个.doc的word文档
    file = open(full_path, 'r+')   
    _num = file.read()
    return int(_num)

###获取到最新的ini配置信息
def getLatestIni(infoArr):
    ###获取版本号中最大的那个版本号 
    if len(infoArr) > 0: 
        maxIniNum = max(infoArr)
        localApkInfo = getApkDownloadUrl(maxIniNum)
        dirPath = Path(LOCAL_DIR)
        if dirPath.exists():
            log.logger.info(LOCAL_DIR + '文件夹已存在')
        else:
            log.logger.info('生成文件夹' + LOCAL_DIR)
            os.mkdir(LOCAL_DIR)    
        downloadFile(localApkInfo['rooturl'] + localApkInfo['apkname'], localApkInfo['apkname'], localApkInfo['reversion'])
        downloadFile(localApkInfo['rooturl'] + localApkInfo['zipname'], localApkInfo['zipname'], localApkInfo['reversion'])
        time.sleep(10)
        # ###将进程全部重启
        # restartProcess()
        ###遍历调用脚本 
        checkScriptState(localApkInfo)
    else:
        log.logger.warning(LOCAL_DATE + "未找到最新的ini文件")

###遍历获取页面基本信息
def getPageInfo():
    r = requests.get(REQUEST_URL + LOCAL_DATE + '/')
    if r.status_code == 200:
        log.logger.debug('brower ' + r.url +  'website success status-code:' + str(r.status_code))
        content = BeautifulSoup(r.content.decode("utf-8"), "html.parser")
        airTestIniArr = []
        for elements in content.find_all("a", href=re.compile("airtest_config")):
            ##正则取出url中的apk版本数字
            airTestIniNum = re.findall('(\d+)',elements.text)
            airTestIniArr.append(airTestIniNum[0])
        getLatestIni(airTestIniArr)
    else:
        log.logger.error('brower ' + r.url +  'website error')

###每次轮询重新赋值全局变量
def initGlobalVar():
    global LOCAL_DATE
    global LOCAL_DIR
    LOCAL_DATE = datetime.now().strftime("%Y%m%d")
    # LOCAL_DATE = '20200909'
    LOCAL_DIR = ROOT_DIR + datetime.now().strftime("%Y%m%d") + '/'
    # counterTxtCreate('0')
    gl._init()
    gl.set_value('counter', 0)
    log.logger.info('counter初始化0')

def intervalTime(inc):
    log.logger.info('-------------------------------------------------------------------')
    log.logger.info(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "执行脚本循环")
    initGlobalVar()
    getPageInfo()
    t = Timer(inc, intervalTime, (inc,))
    t.start()
# 5s

def initFunc():
    log.logger.info('-------------------------------------------------------------------')
    log.logger.info(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "执行脚本")    
    initGlobalVar()
    getPageInfo()

# intervalTime(INTERVAL_VAR)
initFunc()
      




