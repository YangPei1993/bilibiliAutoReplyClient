'''
* author:junqian
* date:2022/12/17 2:26
'''
import os

import requests
import pprint
import re
import random
import time
import json



def get_res(html_url):  # 得到视频的页面数据

    res = requests.get(url=html_url, headers=headers)
    return res


def get_video_bv(html_url):  # 得到视频的bv号
    res = get_res(html_url)

    json_data = res.json()
    v_list = json_data['data']['list']['vlist']
    v_list = [i['bvid'] for i in v_list]  # 列表推导式
    # print(v_list)
    # pprint.pprint(res.json())
    return v_list


def get_video_oid(video_bvid):
    # 获取视频的oid
    video_url = f'https://www.bilibili.com/video/{video_bvid}'
    res = get_res(video_url)
    # \d+ 匹配多个数字
    oid = re.findall('<script>window\.__INITIAL_STATE__={"aid":(\d+),', res.text)[0]
    return oid

def getCommentFromChatGLM(prompt):
    url = "http://localhost:8000/"

    # Data to be sent to the API
    data = {
        "prompt": prompt,
        "history": [],
        "max_length": 32768,
        "top_p": 0.7,
        "temperature": 0.95
    }
    # Send the POST request
    response = requests.post(url, json=data)

    # Print the response
    if response.status_code == 200:
        return json.loads(response.text)['response']
    else:
        return "系统繁忙，请稍后重试"


def comment(oid, parentId, comment):
    content = getCommentFromChatGLM(comment) + "\n ——评论来自chatGLM小助手"
    comment_url = 'https://api.bilibili.com/x/v2/reply/add'  # 通过开发者工具得到评论的接口
    data = {  # 参数
        'csrf': csrf,
        'message': content,
        'oid': oid,
        'plat': 1,
        'type': 1,
        'parent': parentId,
        'root': parentId
    }
    res = requests.post(url=comment_url, headers=headers, data=data)
    status_code_b = res.status_code
    return status_code_b, content

headers = {  # 请求头
    'cookie':"" ,
    'user-agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203"
}
bvid = ""
csrf = ''
oid = get_video_oid(bvid)
maxPage = 100000
file_name = f'G:/workSpace/chatGLMB2/ChatGLM2-6B/replylogs/{bvid}.csv'
if os.path.exists(file_name):
    with open(file_name) as f:
        replayIds = json.load(f)
else:
    replayIds = []
try:
    while True:
        for pn in range(1,maxPage):
            replayUrl = f"https://api.bilibili.com/x/v2/reply?jsonp=jsonp&pn={pn}&type=1&oid={oid}&sort=2"
            replays = get_res(replayUrl).json()['data']['replies']
            if replays is None:
                pn = maxPage
                break
            time.sleep(1)
            for replay in replays:
                replayId = replay['rpid']
                if replayId not in replayIds:
                    status_code, content = comment(oid, replayId, replay['content']['message'])
                    if status_code == 200:
                        print(f'{oid}评论回复成功。')
                        print(f"评论内容：{replay['content']['message']}")
                        print(f"回复内容：{content}")
                        replayIds.append(replayId)
                        print("-----------------------------------------分割线------------------------------------------")
                    else:
                        print(f'{oid}似乎被反爬了')
                    time.sleep(1)
except KeyboardInterrupt:
    # Save replayIds to file when the program is terminated
    with open(file_name, 'w') as f:
        json.dump(replayIds, f)
