import requests
import pathlib
import shutil
import zipfile
import os

# download go-cqhttp and qsign-onekey

if __name__ == '__main__':
    d = pathlib.Path(__file__).parent.joinpath('go-cqhttp')
    try:
        shutil.rmtree(d)
    except FileNotFoundError:
        pass
    d.mkdir()
    print('Downloading go-cqhttp...')
    r = requests.get('https://github.com/Mrs4s/go-cqhttp/releases/download/v1.2.0/go-cqhttp_windows_amd64.exe')
    with open(d / 'go-cqhttp.exe', 'wb') as f:
        f.write(r.content)
    print('Downloading qsign-onekey...')
    r = requests.get('https://github.com/rhwong/qsign-onekey/releases/download/1.1.9-b1/Qsign-Onekey-1.1.9-bitterest-2023-10-25.zip')
    with open(d / 'qsign-onekey.zip', 'wb') as f:
        f.write(r.content)
    # unzip qsign-onekey
    zipfile.ZipFile(d / 'qsign-onekey.zip').extractall(d)
    os.remove(d / 'Qsign-Onekey-1.1.9-bitterest' / 'go-cqhttp.exe')
    os.remove(d / 'Qsign-Onekey-1.1.9-bitterest' / 'go-cqhttp.bat')
    for f in (d / 'Qsign-Onekey-1.1.9-bitterest').iterdir():
        shutil.move(f, d)
    shutil.rmtree(d / 'Qsign-Onekey-1.1.9-bitterest')
    os.remove(d / 'qsign-onekey.zip')
    print('Done.')
