from json import loads
from random import randint
import requests
from multiprocessing import Process, Manager


ENDPOINT = "https://www.google.com/speech-api/full-duplex/v1/"
API_KEY = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"


def __gen_pair():
    r = ''
    for i in range(16):
        r += hex(randint(0, 15))[2:]
    return r.upper()


def __send_audio(data: bytes, pair: str, session):

    parameters = {
        'key': API_KEY,
        'pair': pair,
        'output': 'json',
        'lang': 'en-US',
        'pFilter': '2',
        'maxAlternatives': '1',
        'app': 'chromium',
        'endpoint': '1'
    }

    headers = {'Content-Type': 'audio/x-flac; rate=48000'}
    response = session.post(ENDPOINT+'up', params=parameters, data=data, headers=headers)

    return response



def __recv_reply(pair: str, session, result_buf):

    parameters = {
        'key': API_KEY,
        'pair': pair,
        'output': 'json'
    }

    response = session.get(ENDPOINT+'down', params=parameters)
    result_buf['r'] = response.text


def __ts_start(data: bytes):
    pair = __gen_pair()

    # start both requests simultaneously...
    session = requests.session()
    session.headers.update({'User-Agent': USER_AGENT})

    manager = Manager()
    result_buf = manager.dict()

    # Because of the full-duplex configuration, requests must happen in parallel...
    uploadProc = Process(target=__send_audio, args=(data, pair, session))
    downloadProc = Process(target=__recv_reply, args=(pair, session, result_buf))
    downloadProc.start()
    uploadProc.start()

    uploadProc.join()
    downloadProc.join()

    return result_buf


def transcribe(data: bytes):
    x = __ts_start(data)

    response = loads(x['r'].split('\n')[-2])
    final = response['result'][0]['alternative'][0]

    return final['transcript'], final['confidence']

