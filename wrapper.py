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
        elif self.message.startswith('.xiongwen '):
            return await self.handle_text_generator()
        elif self.message.startswith('.help'):
            return await self.hendle_help()
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
    
    async def handle_text_generator (self):
        text = self.message.split('.xiongwen ')[1]
        anime = text.split(' ')[0]
        keywords = text.split(' ')[1:]
        if not anime or len(keywords) == 0:
            return self.reply_message('请求格式错误')
        print('anime:', anime)
        print('keywords:', keywords)
        with open('gpt-api-key.txt', 'r', encoding='utf-8') as f:
            api_key = f.read()
        async with aiohttp.ClientSession() as session:
            session.headers.update({'Authorization': 'Bearer ' + api_key})
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {
                        'role': 'user',
                        'content': f'以{"、".join(keywords)}为关键词, 生成一篇评价动漫《{anime}》的文章，300字左右'
                    }
                ],
                "temperature": 0.7
            }
            async with session.post('https://api.chatanywhere.com.cn/v1/chat/completions', json=data) as r:
                if r.status != 200:
                    return self.reply_message('无法调用AI API')
                j = await r.json()
        choices = j['choices']
        if not choices or len(choices) == 0:
            return self.reply_message('AI也不知道怎么回答哦')
        choice = choices[0]
        text = choice['message']['content']
        return self.reply_message(text)


    async def hendle_help (self):
        print('handle help')
        return self.reply_message('''
.echo <message> - 回复 <message>
.post <id> - 发布sakugabooru上的动画截图
.xiongwen <anime> <keyword0>  <keyword1> ... - 使用<keyword>作为关键词, 生成一篇关于<anime>的文章
        ''')

