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

headers = {  # 请求头
    'cookie':"buvid3=EBC38A2E-063F-65EF-A0FD-A3A9B02BA27A35416infoc; b_nut=1682781535; _uuid=C9E1059D4-FEB9-144E-9F1010-648893C6453736895infoc; buvid4=149008DE-C709-3C18-887C-CB9236F254BA36522-023042923-KxfNF8XJX%2FbdveSLP4EbSg%3D%3D; CURRENT_PID=292531e0-e6a1-11ed-b73e-4192409d8aef; rpdid=|(k|kmJlJlRk0J'uY)k~)ulJY; DedeUserID=43127022; DedeUserID__ckMd5=ed4444d1ec5adf4e; nostalgia_conf=-1; hit-new-style-dyn=1; hit-dyn-v2=1; i-wanna-go-back=-1; b_ut=5; FEED_LIVE_VERSION=V8; header_theme_version=CLOSE; buvid_fp_plain=undefined; CURRENT_FNVAL=4048; share_source_origin=copy_web; bsource=search_baidu; home_feed_column=5; browser_resolution=1707-857; bili_ticket=eyJhbGciOiJFUzM4NCIsImtpZCI6ImVjMDIiLCJ0eXAiOiJKV1QifQ.eyJleHAiOjE2OTMyMzM3NzUsImlhdCI6MTY5Mjk3NDU3NSwicGx0IjotMX0.eYprAzON2en8Lv76qd-IqgoTeqLrViEpnwWm565e33Uj9OFmpcw_C2Wr4UZGj-X9klAKQITLKyvkUUP0r7juD_DW-AXJBNxqH1Z0mpHhm6yCZ-5-CmCOscx8ysvdvBd5; bili_ticket_expires=1693233775; SESSDATA=1eef6e4c%2C1708526589%2C675d3%2A81bOw7DbB0h_xy0lJvAl3K34nROKApvqDMHAtP2jUOpikwgweI6jXde0hkG7Wn-9X5L-O0SgAAFgA; bili_jct=34885214a98de3d524d01db8e5c54287; sid=6e15lod9; bp_video_offset_43127022=834032148667170818; CURRENT_QUALITY=80; PVID=1; fingerprint=14454368b76f3360074bb3efa4e3d3a1; buvid_fp=14454368b76f3360074bb3efa4e3d3a1; b_lsid=88585710F_18A35E68F98" ,
    'user-agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203"
}


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


bvid = "BV19r4y1R7Ja"
csrf = '34885214a98de3d524d01db8e5c54287'
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
