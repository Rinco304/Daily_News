# -*- coding: utf-8 -*-
import os
import json
import aiohttp
import aiofiles
import asyncio
import hoshino

from pathlib import Path
from typing import List
from hoshino import Service,priv
from hoshino.typing import CQEvent

# 调用api获取
api = 'https://api.03c3.cn/api/zb'
file_path = './hoshino/modules/Daily_News/imgs'
file_me = '60s'

# 群订阅列表
data_path = Path("hoshino/modules/Daily_News")
sub_data_path = data_path / "sub_group_data.json"

# 调用api获取
async def download_image():
    image_url = api
    print('正在下载资源')
    try:
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        file_name = os.path.join(file_path, 'today.png')
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_name, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            await f.write(chunk)
                    print("Download Successful！")
                else:
                    print("Failed to download image")
    except Exception as e:
        print("Exception:", str(e))

if __name__ == '__main__':
    import asyncio
    asyncio.run(download_image())


sv_help = '''
[订阅每日新闻] 启用后会在每天早上发送一份每日新闻
[取消订阅每日新闻] 取消订阅
[每日新闻] 手动发送一份新闻
[更新每日新闻] 手动更新新闻图片（仅限维护组使用）
订阅功能后会在每天9.30自动发送一份新闻图片
'''.strip()

sv = Service(
    name='每日新闻',
    enable_on_default=True,
    visible=True,
    bundle="娱乐",
    help_=sv_help
)

@sv.on_fullmatch(('今日新闻','每日新闻','新闻60秒','新闻60s'))
async def Daily_News(bot, ev:CQEvent):
    tdimg = 'today' + ".png" 
    image_path = os.path.join(os.path.dirname(__file__),'imgs/',tdimg)
    # print (image_path)
    try:
        await download_image()
        await bot.send(ev, f'[CQ:image,file=file:///{image_path}]')
        # time.sleep(2)
        # await bot.send(ev,'数据来源:澎湃、人民日报、腾讯新闻、网易新闻、新华网、中国新闻网；每日凌晨1时后更新')
    except:
        await bot.send(ev, '获取失败，请重试或联系管理员')

@sv.scheduled_job('cron', hour='09', minute='30', jitter=50)
async def autoNews():
    tdimg = 'today' + ".png"
    image_path = os.path.join(os.path.dirname(__file__),'imgs/',tdimg)
    try:
        await download_image()
        # 查询是否是订阅群，如果是就发送消息，不是就不发送
        sub_group_list = load_sub_list()
        for gid in sub_group_list['group_list']:
            message = f'[CQ:image,file=file:///{image_path}]'
            await sv.bot.send_group_msg(group_id=gid, message=message)
            await asyncio.sleep(5)
    except Exception as e:
        bot = hoshino.get_bot()
        sid = hoshino.get_self_ids() # 获取bot账号列表
        superid = hoshino.config.SUPERUSERS[0]
        await bot.send_private_msg(self_id=sid, user_id=superid, message=f"下载每日新闻图片失败，请重新获取\n{e}")


@sv.on_fullmatch("订阅每日新闻")
async def sub_group(bot, ev):
    gid = ev.group_id
    u_priv = priv.get_user_priv(ev)
    if u_priv >= sv.manage_priv:
        try:
            sub_group_list = load_sub_list()
            if gid in sub_group_list['group_list']:
                await bot.send(ev, "本群已订阅此功能")
                return
            sub_group_list['group_list'].append(gid)
            dump_sub_list(sub_group_list)
            await bot.send(ev, "订阅成功~")
        except Exception as e:
            await bot.send(ev, f"出现错误:{e}")
    else:
        await bot.send(ev, "只有管理以上才能使用此指令哦")


@sv.on_fullmatch("取消订阅每日新闻")
async def unsub_group(bot, ev):
    gid = ev.group_id
    u_priv = priv.get_user_priv(ev)
    if u_priv >= sv.manage_priv:
        try:
            sub_group_list = load_sub_list()
            if gid not in sub_group_list['group_list']:
                await bot.send(ev, "此群没有订阅此功能")
                return
            sub_group_list['group_list'].remove(gid)
            dump_sub_list(sub_group_list)
            await bot.send(ev, "取消订阅成功~")
        except Exception as e:
            await bot.send(ev, f"出现错误:{e}")
    else:
        await bot.send(ev, "只有管理以上才能使用此指令哦")


def dump_sub_list(sub_group_list: List[int]):
    # sub_data_path.mkdir(parents=True, exist_ok=True)
    json.dump(
        sub_group_list,
        sub_data_path.open("w", encoding="utf-8"),
        indent=4,
        separators=(",", ": "),
        ensure_ascii=False,
    )

def load_sub_list() -> List[int]:
    if sub_data_path.exists():
        with sub_data_path.open("r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.decoder.JSONDecodeError:
                print("订阅列表解析错误，将重新获取")
                sub_data_path.unlink()
    return {"group_list":[]}