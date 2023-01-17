from escpos.constants import PAPER_PART_CUT
from escpos.printer import Usb
from datetime import datetime
from PIL import Image
import os
import asyncio
import websockets
import json
import requests
from io import BytesIO
from typing import Optional

P_continue = False


def title(p: Usb, text, **kwargs):
    p.set(text_type='B', width=2, align='CENTER', **kwargs)
    p.text(text)
    p.set()


def header(
        p: Usb,
        time: datetime = datetime.now(),
        title: Optional[str] = None,
        priority: int = 3):
    if title:
        style = []

        if priority > 1:
            # just make sure this is a title
            style.append(b'* ')
        if priority > 2:
            # underlined (1px)
            style.append(b'\x1B\x2D\x01')
        if priority > 3:
            # emphasized
            style.append(b'\x1B\x45\x01')
        if priority > 4:
            # inverted and two beeps
            style.append(b'\x1D\x42\x01')
            style.append(b'\x1B\x42\x02\x01')
        if priority == 5:
            # Double height and two more beeps
            style.append(b'\x1D\x21\x01')
            style.append(b'\x1B\x42\x02\x01')

        p._raw(b''.join(style))

        t = title.encode('euckr', 'replace')
        p._raw(t)
        if len(t) % 42 < 12:
            # Not enough space for display the time so feed it
            # Hint: 42 'font-A' characters in a line
            p._raw(b'\n')

    # p.set(align="RIGHT", font="b")
    p.set(font="b")
    p._raw(b'\x1B\x24\xb0\x01')  # move to 432(0x1b0) from line start
    p.text(time.strftime('%Y-%m-%d %H:%M')+"\n")
    p.set()


def footer(p: Usb):
    p._raw(b"\n")
    p.set(align="CENTER", font="b")
    p.text("-*-")

    p._raw(b"\n\n\n\n")
    # p.cut()
    p.set(align="RIGHT", text_type="BU")
    p.text("    Printer.lapy ")
    p.set(align="RIGHT")
    p.text(" * \n")
    p.set()
    p._raw(PAPER_PART_CUT)


async def pprint(p: Usb, body):
    time = datetime.fromtimestamp(body['time'])
    title = '제목 없는 메시지'
    priority = 3
    tags = []

    if 'title' in body:
        title = body['title']
    if 'priority' in body:
        priority = body['priority']
    if 'tags' in body:
        tags = body['tags']

    # --
    
    # header
    if 'noheader' not in tags \
            or not p_continue:
        header(p, time, title, priority)

    # attachment
    if 'attachment' in body:
        supported_formats = [
            'image/apng',
            'image/png',
            'image/jpg',
            'image/jpeg',
            'image/gif',
            'image/bmp',
            'unknown'
        ]
        url = body['attachment']['url']
        try:
            filetype = body['attachment']['type']
        except KeyError:
            filetype = 'unknown'

        try:
            filename = body['attachment']['name'].strip()
        except KeyError:
            filename = ''

        # region rawfile
        if 'rawfile' in tags:
            res = requests.get(url)
            if len(res.content) < 1024*32:
                p._raw(res.content)
            else:
                p._raw(b'\x1d\x42\x01')
                p._raw(b'Payload is too big' + b'\n')
                p._raw(b'\x1d\x42\x00')
                print('Too big payload:', filename, len(res.content))
        # endregion

        # region image
        elif filetype in supported_formats:
            p.set(align="CENTER")

            try:
                res = requests.get(url)
                img = Image.open(BytesIO(res.content))
                maxsize = (576, 576)
                if max(img.width, img.height) > maxsize[0]:
                    ratio = img.width / img.height
                    size = (maxsize[0], int(maxsize[1]/ratio))
                    img = img.resize(size)

                p.image(img, impl="bitImageColumn")
                img.close()
                res.close()

            except Exception as e:
                p._raw(b'\x1d\x42\x01')
                p._raw(str(e).encode('euckr', 'replace') + b'\n')
                # p._raw(b'\x1d\x42\x00')
                print(url, ':', e)
        # endregion

        if 'notext' not in tags \
                or filename != '':
            p.set(align="CENTER", font="b")
            p._raw(b'(' + filename.encode('euckr', 'replace') + b')\n')
        p.set()

    # body
    if 'notext' not in tags:
        p._raw(body['message'].encode('euckr'))

    # footer
    if 'continue' in tags:
        p_continue = True
    else:
        p_continue = False

    if not p_continue and 'nofooter' not in tags:
        footer(p)


async def loopever(p: Usb):
    url = f"wss://{ os.environ['NTFY_BASE'] }/"
    url += os.environ['NTFY_TOPIC']
    url += "/ws"
    url += "?since=" + str(int(datetime.now().timestamp()))

    async with websockets.connect(url) as websocket:
        print("ready.")
        while True:
            res = await websocket.recv()
            body = json.loads(res)

            if body['event'] == 'message':
                await pprint(p, body)
            # print(body['text'])


def main():
    try:
        usb_vid = int(os.environ['USB_VID'], 0)
        usb_pid = int(os.environ['USB_PID'], 0)
        p = Usb(usb_vid, usb_pid)
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(loopever(p))
        loop.run_forever()

    finally:
        p.close()


if __name__ == "__main__":
    main()