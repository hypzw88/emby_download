import requests
import json
import os
import time
import configparser

file = 'config.ini'
# 创建配置文件对象
config = configparser.ConfigParser()
# 读取文件
config.read(file, encoding='utf-8')

# 下载路径
download_path = config['download']['download_path']

# emby配置
url = config['emby']['url']
username = config['emby']['username']
password = config['emby']['password']
api_key = config['emby']['api_key']
user_id = config['emby']['user_id']


# 获取媒体信息类型
def main(mediaId):
    response = json.loads(requests.get(f"{url}/emby/Users/{user_id}/Items/{mediaId}?api_key={api_key}").text)
    print(f"媒体类型： {response['Type']}")
    if(response['Type'] == 'Movie'):# 电影
        print(f"电影名称： {response['Name']}  年份：{response['ProductionYear']}\nFileName： {response['FileName']}")
        getDownloadInfo(response['Name'],"",mediaId)
    elif(response['Type'] == 'Series'):# 整部剧集
        print(f"剧集名称： {response['Name']}  年份：{response['ProductionYear']}")
        print(f"季数：  共 {response['ChildCount']} 季")
        re = json.loads(requests.get(f"{url}/emby/Shows/{mediaId}/Seasons?api_key={api_key}").text)['Items']
        for item in re:
            print(f"剧集：【{item['SeriesName']}】    季： {item['Name']}   Id： {item['Id']}")
        if(len(re) == 1):
            ok = input("当前剧集共1季，是否确认下载(y/n)：") or "y"
            if(ok == 'y'):
                getEpisodesInfo(mediaId,re[0]['Id'])
            else:
                print("取消下载")
        else:
            inputSeasonNum = input("请输入需要下载的IndexNumber(1,2,3具体下载某一季，输入a下载所有季)：") or "a"
            if(inputSeasonNum.isdigit()):
                print(f"当前下载第 {inputSeasonNum} 季")
                inputSeasonNum = int(inputSeasonNum) - 1
                getEpisodesInfo(mediaId,re[inputSeasonNum]['Id'])
            elif(inputSeasonNum == 'a' or inputSeasonNum == 'A'):
                print("当前下载所有季")
                for x in re:
                    getEpisodesInfo(mediaId,x['Id'])

    elif(response['Type'] == 'Season'):# 剧集中的某一季
        print(f"剧集名称： {response['SeriesName']}  年份：{response['ProductionYear']}")
        print(f"集数：  共 {response['ChildCount']} 集")
        ok = input("是否确认下载(y/n)：") or "y"
        if(ok == 'y'):
            getEpisodesInfo(response['ParentId'],response['Id'])
        else:
            print("取消下载")
    elif(response['Type'] == 'Episode'):# 季中的某一集
        print(f"剧集名称： {response['SeriesName']}  年份：{response['ProductionYear']}")
        print(f"当前下载： {response['SeriesName']} - {response['SeasonName']} - 第 {response['IndexNumber']} 集 - {response['Name']}")
        getDownloadInfo(response['SeriesName'],response['SeasonName'],response['Id'])
    else:
        print("媒体类型错误")
          
# 获取季信息
def getEpisodesInfo(tvId,SeasonId):
    response = json.loads(requests.get(f"{url}/emby/Shows/{tvId}/Episodes?SeasonId={SeasonId}&Limit=1000&ImageTypeLimit=1&UserId={user_id}&api_key={api_key}").text)
    for x in response['Items']:
        SeriesName = x['SeriesName']
        SeasonName = x['SeasonName']
        Name = x['Name']
        IndexNumber = x['IndexNumber']
        Id = x['Id']
        print(f"当前下载： {SeriesName} - {SeasonName} - 第 {IndexNumber} 集 - {Name}")
        getDownloadInfo(SeriesName,SeasonName,Id)

# 获取播放信息
def getDownloadInfo(MediaName,SeasonName,Id):
    response = json.loads(requests.get(f"{url}/emby/Items/{Id}/PlaybackInfo?UserId={user_id}&api_key={api_key}").text)
    for x in response['MediaSources']:
        Name = x['Name']
        Container = x['Container']
        MediaSourcesId = x['Id']
        playUrl = f"{url}/videos/{Id}/stream.{Container}?api_key={api_key}&MediaSourceId={MediaSourcesId}&Static=true" 
        fileSize = x.get('Size', '')
        if (fileSize != ''):
            fileSize = str(round(fileSize / 1024 / 1024, 2)) + ' MB' #兆字节
            print(f"文件大小：{fileSize}")
        print(f"下载地址： {playUrl}")
        savePath = f"/{MediaName}/{SeasonName}"
        saveName = f"/{Name}.{Container}"
        downloadProgressbar(playUrl, savePath, saveName)

def getPlayerUrl(Id):
    response = json.loads(requests.get(f"{url}/emby/Items/{Id}/PlaybackInfo?UserId={user_id}&api_key={api_key}").text)
    for x in response['MediaSources']:
        Name = x['Name']
        Container = x['Container']
        MediaSourcesId = x['Id']
        playUrl = f"{url}/videos/{Id}/stream.{Container}?api_key={api_key}&MediaSourceId={MediaSourcesId}&Static=true" 
        fileSize = x.get('Size', '')
        if (fileSize != ''):
            fileSize = str(round(fileSize / 1024 / 1024, 2)) + ' MB' #兆字节
            print(f"文件大小：{fileSize}")
        print(f"播放地址： {playUrl}")

def downloadProgressbar(downloadUrl,savePath,saveName):
    savePath = download_path + savePath
    if not os.path.exists(savePath): # 看是否有该文件夹，没有则创建文件夹
        os.makedirs(savePath)
    start = time.time() #下载开始时间
    response = requests.get(downloadUrl, stream=True)
    size = 0 #初始化已下载大小
    chunk_size = 1024 # 每次下载的数据大小
    content_size = int(response.headers['content-length']) # 下载文件总大小

    try:
        if response.status_code == 200: #判断是否响应成功
            print('Start download,[File size]:{size:.2f} MB'.format(size = content_size / chunk_size /1024)) #开始下载，显示下载文件大小
            filepath = savePath+saveName #设置图片name，注：必须加上扩展名
            with open(filepath,'wb') as file: #显示进度条
                for data in response.iter_content(chunk_size = chunk_size):
                    file.write(data)
                    size +=len(data)
                    print('\r'+'[下载进度]:%s%.2f%%' % ('>'*int(size*50/ content_size), float(size / content_size * 100)) ,end=' ')
            end = time.time() #下载结束时间
            print('Download completed!,times: %.2f秒' % (end - start)) #输出下载用时时间
    except:
        print('Error!')

def login():
    global user_id
    global api_key
    if(api_key == ""):
        data = (('Username', username),
                ('Pw', password),)
        response = json.loads(requests.post(url + "/emby/Users/authenticatebyname?X-Emby-Client=Emby%20Web&X-Emby-Device-Id=1e202193-5444-4556-9f5a-adf97faa0735&X-Emby-Client-Version=4.7.11.0&X-Emby-Language=zh-cn",data=data).text)
        # print(response['User']['Id'])# user_id
        # print(response['AccessToken'])# api_key
        user_id = response['User']['Id']
        api_key = response['AccessToken']
        config.set('emby','user_id',response['User']['Id']) #这些操作只是将文件内容读取到了内存中，必须写回文件才能生效，写回采用configparser的write方法 config.write(open("ini", "w"))
        config.set('emby','api_key',response['AccessToken']) #这些操作只是将文件内容读取到了内存中，必须写回文件才能生效，写回采用configparser的write方法 config.write(open("ini", "w"))
        config.write(open(file,'w'))
     
def search(keyword):
    response = json.loads(requests.get(f"{url}/emby/Users/{user_id}/Items?SortBy=SortName&SortOrder=Ascending&Fields=BasicSyncInfo,CanDelete,Container,PrimaryImageAspectRatio,ProductionYear,Status,EndDate&StartIndex=0&EnableImageTypes=Primary,Backdrop,Thumb&ImageTypeLimit=1&Recursive=true&SearchTerm={keyword}&GroupProgramsBySeries=true&Limit=50&api_key={api_key}").text)
    if(len(response['Items']) == 0):
        print("未搜索到相关数据")
        return
    for x in response['Items']:
        print(f"ID： {x['Id']}    剧集名称：{x['Name']}    类型：{x['Type']}    年份：{x.get('ProductionYear', '未知年份')}")
     
    mediaId = input("请输入需要下载媒体资源ID：\n")
    main(mediaId)

if __name__ == '__main__':
    response = json.loads(requests.get(f"{url}/emby/system/info/public").text)
    print("emby地址："+url)
    print("媒体库："+response['ServerName'])
    login()
    print("1、直接输入媒体ID下载\n2、关键词搜索下载\n3、根据媒体ID获取播放地址：\n")
    option = input("请选择下载方式：\n")
    if(option == '1'):
        mediaid = input("请输入媒体id：\n")
        main(mediaid)
    elif(option == '2'):
        keyword = input("请输入搜索关键词：\n")
        search(keyword)
    elif(option == '3'):
        keyword = input("请输入媒体id： \n")
        getPlayerUrl(keyword)