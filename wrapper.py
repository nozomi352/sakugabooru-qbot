from typing import *
import aiohttp

class InputMessageWrapper:
    my_qq = -1
    http_url = ''

    def __init__ (self, msg: dict):
        self.message: str = msg['message']
        self.sender_qq = msg['sender']['user_id']
        self.group_id = msg['group_id']
        self.raw_message = msg['raw_message']

    def send_message (self, message: str):
        return {
            'action': 'send_group_msg',
            'params': {
                'group_id': self.group_id,
                'message': message
            }
        }
    
    def reply_message (self, message: str):
        return {
            'action': 'send_group_msg',
            'params': {
                'group_id': self.group_id,
                'message': f'[CQ:at,qq={self.sender_qq}] {message}'
            }
        }

    async def process (self):
        if self.message.startswith('.echo '):
            return self.handle_echo()
        elif self.message.startswith(f'[CQ:at,qq={self.my_qq}]'):
            return self.handle_greetings()
        elif self.message.startswith('.post '):
            return await self.handle_sakuga_booru_post()
        else:
            return None

    def handle_echo (self):
        rep = self.message.split('.echo ')[1]
        return self.send_message(rep)
    
    def handle_greetings (self):
        return self.reply_message('你好')

    async def handle_sakuga_booru_post (self):
        post_id = self.message.split('.post ')[1]
        print('sakugabot.pw', post_id)
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://sakugabot.pw/api/posts/{post_id}/?format=json') as r:
                if r.status != 200:
                    return self.reply_message(f'无法调用sakugabot.pw API, ID: {post_id}')
                j = await r.json()
        tags: List[Dict] = j['tags']
        display_tags = '; '.join([item['main_name'] for item in tags if item['type'] == 3 or item['type'] == 1])
        weibo = j['weibo']
        if not weibo:
            return self.reply_message(f'无法获取wb链接, ID: {post_id}')
        weibo_img_url = weibo['img_url']
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://' + InputMessageWrapper.http_url + '/download_file',
                data={'url': weibo_img_url, 'headers':'Referer=https://weibo.com/'}
            ) as r:
                if r.status != 200:
                    return self.reply_message(f'无法获取wb图片, ID: {post_id}')
                j = await r.json()
        weibo_img_url = j['data']['file']
        print('file url:', weibo_img_url)
        return self.reply_message(f'{post_id}\n[CQ:image,file=file:///{weibo_img_url}] {display_tags}')
