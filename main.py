import fastapi
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from typing import *
from wrapper import InputMessageWrapper
import json
import threading
import asyncio
import time

app = fastapi.FastAPI()

@app.websocket('/ws')
async def handle_message(websocket: WebSocket):
    if websocket.client.host == '127.0.0.1':
        await websocket.accept()
    else:
        await websocket.close()
        return
    messages_in = []
    messages_out = []
    running = threading.Event()

    async def recv_message(ev: threading.Event):
        try:
            while not ev.is_set():
                data = await websocket.receive_json()
                if data.get('post_type', '') != 'message':
                    continue
                messages_in.append(data)
                await asyncio.sleep(1e-5)
        except WebSocketDisconnect:
            ev.set()

    async def send_message(ev: threading.Event):
        try:
            while not ev.is_set():
                messages = messages_out.copy()
                messages_out.clear()
                for message in messages:
                    await websocket.send_json(message)
                await asyncio.sleep(1e-5)
        except WebSocketDisconnect:
            ev.set()
    
    async def process_message(ev: threading.Event):
        try:
            while not ev.is_set():
                messages = messages_in.copy()
                messages_in.clear()
                for message in messages:
                    msg = InputMessageWrapper(message)
                    res = await msg.process()
                    if res:
                        messages_out.append(res)
                await asyncio.sleep(1e-5)
        except WebSocketDisconnect:
            ev.set()

    await asyncio.gather(recv_message(running), send_message(running), process_message(running))

if __name__ == '__main__':
    import uvicorn
    import yaml
    with open('go-cqhttp/config.yml', 'r', encoding='utf-8') as f:
        decoded = f.read()
    config = yaml.load(decoded, Loader=yaml.FullLoader)
    config_servers: List[Dict] = config['servers']
    url_item = [item for item in config_servers if item.get('ws-reverse')][0]
    url = url_item['ws-reverse']['universal']\
        .replace('/ws', '')\
        .replace('ws://', '')\
        .replace('wss://', '')
    host = url.split(':')[0]
    port = int(url.split(':')[1])
    print(f'ws url: {url}')

    account: Dict = config['account']
    InputMessageWrapper.my_qq = account['uin']
    print(f'my qq: {InputMessageWrapper.my_qq}')

    http_item = [item for item in config_servers if item.get('http')][0]
    InputMessageWrapper.http_url = http_item['http']['address']

    uvicorn.run('main:app', host=host, port=port, log_level='info')
