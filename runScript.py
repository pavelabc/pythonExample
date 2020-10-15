import os, sys
from pathlib import Path
import subprocess
import requests
from bs4 import BeautifulSoup
import bs4
import re
###ini文件读取模块
import configparser
import urllib
from datetime import datetime
from threading import Timer
import time
import globalVar as gl
#APK_PATH = '/home/yunce/airtest-auto/' + datetime.now().strftime("%Y%m%d") + '/'
PUSH_PATH = ' /sdcard/Android/data/com.tencent.qyn/files/'
ROOT_PATH = '/home/yunce/apks/'


###log类占位
class log:
    pass


def init(serial,taskApkPath,taskFilesPath,taskPackageName,taskVersion,modelName,classLog):
    ##对log类进行重新赋值
    global log
    log = classLog
    ##开始正式逻辑
    log.logger.info('%s开始检查版本！' %serial)
    localApkVersion = valiApkVersion(serial,taskPackageName)
    log.logger.info('%s localApkVersion is %s' %(serial,localApkVersion))
    log.logger.info('%s taskVersion is %s'  %(serial,taskVersion))
    if localApkVersion != taskVersion:
        log.logger.info('%s生成占用文件！' %serial)
        scriptPath = '/home/yunce/airtest-auto/'+serial
        text_create(scriptPath, serial)
        if(localApkVersion != ''):
            uninstallApk(serial,taskPackageName)
            log.logger.info('%s安装前预卸载！' %serial)
            time.sleep(10)
        log.logger.info('%s安装开始！' %serial)
        insertApk(serial,taskApkPath)
        log.logger.info('%s安装结束！' %serial)
        time.sleep(5)
        startApk(serial,taskPackageName)
        log.logger.info('%s启动结束！' %serial)
        time.sleep(4*60)
        closeApk(serial,taskPackageName)
        log.logger.info('%s关闭游戏' %serial)
        pushFiles(serial,taskFilesPath)
        log.logger.info('%s推送push文件结束！' %serial)
        taskName = get_task_name(serial)
        taskId = getTaskId(serial,taskPackageName,taskVersion,taskName)
        log.logger.info('%s获取任务ID结束！ id=%s' %(serial,taskId))
        logPath = ROOT_PATH + taskId + '/'+ modelName +'-'+serial+'/airTestLog'
        makeReportDir(logPath)
        log.logger.info('%s生成airTest报告文件夹=%s' %(serial,logPath))
        startAirtest(serial,scriptPath+'/index.air',logPath+'/1')
        log.logger.info('%s设备airtest运行结束！' %serial)
        time.sleep(10)
        startAirtestReport(serial,scriptPath +'/index.air',logPath+'/1')
        log.logger.info('%s生成报告结束！' %serial)
        finishTask(serial,taskId,logPath)
        log.logger.info('%s调用finish接口' %serial)
        sendMail(serial,taskId,logPath)
        log.logger.info('%s调用sendMail接口' %serial)
        closeApk(serial,taskPackageName)
        log.logger.info('%s任务结束-关闭游戏' %serial)
        del_txt(scriptPath, serial)
        log.logger.info('%s删除占用文件！' %serial)
    else:
        log.logger.info('devices %s apk %s version is latest' %(serial,taskPackageName))

def text_create(scriptPath, serial):
    full_path = scriptPath + '/'+ serial + '.txt'  # 也可以创建一个.doc的word文档
    file = open(full_path, 'w')
    file.write(serial)

#根据imei获取测试名称
def get_task_name(serial):
    if serial == 'E6E4C20420026353':
        return '活动、心法、招式模块'
    elif serial == '66B0220226000709':
        return '鉴察院活动、帮派、装备模块'
    elif serial == 'MDX0220814027217':
        return 'ui遍历模块'
    else:
        return '定制自动化循环测试'

def del_txt(scriptPath, serial):
    path = scriptPath + '/' + serial + '.txt'  # 文件路径
    if os.path.exists(path):  # 如果文件存在
    # 删除文件，可使用以下两种方法。
        os.remove(path)  
    #os.unlink(path)
    else:
        log.logger.info('no such file:%s.txt！' %serial)

#gpus = sys.argv[1]
#判断版本
##验证当前设备的apk版本信息
def valiApkVersion(serial,packageName):
    p = subprocess.Popen('adb -s ' + serial  + ' shell dumpsys package ' + packageName + ' | grep versionName', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,close_fds=True)
    # 判断命令是否执行成功
    output, err = p.communicate()
    status = 1 if err else 0
    output = output.decode("utf-8")
    if status == 0 and output != '':
        log.logger.info('adb -s %s shell dumpsys package %s | grep versionName' %(serial, packageName))
        log.logger.debug(output)
        output = output.replace('\n','')
        output = output.replace(" ", "").split('=')
        log.logger.info('device %s package %s version is %s' %(serial, packageName, output[1]))
        return output[1]
    else:
        log.logger.error('adb -s %s shell dumpsys package %s | grep versionName' %(serial, packageName))
        log.logger.debug(err)
        return ''
    
def counterTxtModify():
    full_path = '/home/yunce/airtest-auto/counter.txt'  # 也可以创建一个.doc的word文档
    file = open(full_path, 'r+')
    _num = file.read()
    _num = int(_num) - 1
    log.logger.debug("当前counter值为%s" %_num)
    file.close()

    file1 = open(full_path, 'w+')
    file1.write(str(_num))
    file1.close()



#开始安装
def insertApk(serial,apkName):
    log.logger.info('device %s 开始安装：' %serial)
    log.logger.info('安装命令：'+'adb -s ' + serial  + ' install ' + apkName)
    p = subprocess.Popen('adb -s ' + serial  + ' install ' + apkName, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,close_fds=True)
    output, err = p.communicate()
    status = 1 if err else 0
    if status == 0:
        log.logger.info('adb -s %s install %s ' %(serial, apkName))
        _counter = gl.get_value('counter')
        _counter = _counter - 1
        gl.set_value('counter', _counter)
        log.logger.info('counter值为%s' % _counter)
        log.logger.debug(output)
    else:
        log.logger.error('adb -s %s  install %s '  %(serial, apkName))
        log.logger.debug(err)
    return status, output

#开始卸载
def uninstallApk(serial,packageName):
    p = subprocess.Popen('adb -s ' + serial  + ' uninstall ' + packageName, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,close_fds=True)
    output, err = p.communicate()
    status = 1 if err else 0
    if status == 0:
        log.logger.info('adb -s %s uninstall %s ' %(serial, packageName))
        log.logger.debug(output)
    else:
        log.logger.error('adb -s %s  uninstall %s '  %(serial, packageName))
        log.logger.debug(err)
    return status, output

#启动游戏
def startApk(serial,packageName):
    p = subprocess.Popen('adb -s ' + serial  + ' shell monkey -p ' + packageName +' -c android.intent.category.LAUNCHER 1', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, err = p.communicate() 
    status = 1 if err else 0
    if status == 0:
        log.logger.info('adb -s %s  shell monkey -p  %s -c android.intent.category.LAUNCHER 1' %(serial, packageName))
        output = output.decode("utf-8").replace(" ", "").split('=')
    else:
        log.logger.error('adb -s %s  shell monkey -p  %s -c android.intent.category.LAUNCHER 1'  %(serial, packageName))
        log.logger.debug(err)
    return status, output     

#关闭游戏
def closeApk(serial,packageName):
    p = subprocess.Popen('adb -s ' + serial  + ' shell am force-stop ' + packageName, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, err = p.communicate() 
    status = 1 if err else 0
    if status == 0:
        log.logger.info('adb -s %s  shell am force-stop  %s' %(serial, packageName))
        output = output.decode("utf-8").replace(" ", "").split('=')
    else:
        log.logger.error('adb -s %s  shell am force-stop  %s'  %(serial, packageName))
        log.logger.debug(err)
    return status, output 

#发送文件到手机
def pushFiles(serial,fileName):
    log.logger.info('准备开始adb push %s' % serial)
    p = subprocess.Popen('adb -s ' + serial  + ' push ' + fileName+' '+PUSH_PATH, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, err = p.communicate() 
    status = 1 if err else 0
    if status == 0:
        log.logger.info('adb -s %s push %s ' %(serial,fileName+' '+PUSH_PATH))
        output = output.decode("utf-8").replace(" ", "").split('=')
    else:
        log.logger.error('adb -s %s push %s ' %(serial,fileName+' '+PUSH_PATH))
        log.logger.debug(err)
    return status, output  

#生成airtestReport的文件夹
def makeReportDir(logPath):
    os.makedirs(logPath)


#开始airtest
def startAirtest(serial,scriptPath,logPath):
    log.logger.info('开始执行%s的airtest脚本任务' %serial)
    p = subprocess.Popen('airtest run ' +scriptPath +' --device Android:///' + serial  + '?ori_method=ADBORI --log ' + logPath + ' --recording', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, err = p.communicate() 
    status = 1 if err else 0
    if status == 0:
        log.logger.info('airtest run %s --device Android:///%s?ori_method=ADBORI --log %s + --recording'  %(scriptPath, serial,logPath))
        output = output.decode("utf-8").replace(" ", "").split('=')
    else:
        log.logger.error('airtest run %s --device Android:///%s?ori_method=ADBORI --log %s --recording'  %(scriptPath, serial,logPath))
    return status, output  

#生成测试报告
def startAirtestReport(serial,scriptPath,logPath):
    yunce_path = logPath.replace('/home/yunce/apks', '/air-test/images') + '/index.log/'
    p = subprocess.Popen('airtest report ' +scriptPath +' --log_root ' + logPath  + ' --export ' + logPath + ' --yunce_path ' + yunce_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, err = p.communicate() 
    status = 1 if err else 0
    if status == 0:
        log.logger.info('airtest report %s --log_root %s  --export %s --yunce_path %s '  %(scriptPath, logPath,logPath,yunce_path))
        output = output.decode("utf-8").replace(" ", "").split('=')
    else:
        log.logger.error('airtest report %s --log_root %s  --export %s --yunce_path %s '  %(scriptPath, logPath,logPath,yunce_path))
        log.logger.debug(err)
    return status, output  

#获取任务ID
def getTaskId(serial,packageName,version,taskName):
    url = 'http://10.246.86.36/data/getTask'
    param = '?imei='+serial+'&packageName='+packageName+'&version='+version+'&taskName='+taskName
    r = requests.get(url+param)
    log.logger.info('调用getTaskId接口%s' %url+param)
    log.logger.info(r.text)
    return r.text

#调用finish接口
def finishTask(serial,taskId,logPath):
    url = 'http://10.246.86.36/data/finish'
    param = '?imei='+serial+'&taskId='+taskId+'&path='+logPath+'&repeatNum=1'
    log.logger.info('调用finishTaskd接口%s' %url+param)
    r = requests.get(url+param)
    log.logger.info(r.text)
    return r.text


def sendMail(serial,taskId,logPath):
    url = 'http://10.246.86.36/data/sendMail'
    param = '?imei='+serial+'&taskId='+taskId+'&path=' + logPath +'&repeatNum=1'
    log.logger.info('调用sendMail接口%s' %url+param)
    r = requests.get(url+param)
    log.logger.info(r.text)
    return r.text


#serial=sys.argv[1]
#apkName=sys.argv[2]
# taskId = getTaskId('45749a6','庆余年','1.2.1.2305','庆余年定制自动化循环测试')
# print('taskId = '+taskId)
# valiApkVersion('45749a6','com.tencent.qyn')
# serial = '45749a6'
# scriptPath = '/home/yunce/airtest-auto/'+serial

#del_txt(scriptPath, serial)
