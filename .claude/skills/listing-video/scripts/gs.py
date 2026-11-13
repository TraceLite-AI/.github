#!/usr/bin/env python3
"""GlobalStore 模型中心任务接口的小客户端（图片 / 配音 / 视频都走同一个接口）。

密钥只从环境变量 GLOBALSTORE_API_KEY 读取，不要写进文件或提交到 git。
任务文件默认放在当前目录的 job/ 下，可用环境变量 GS_JOB_DIR 改。

用法:
  gs.py balance                          查余额
  gs.py submit <名字> <请求体.json>        提交任务，保存 job/<名字>.task.json
  gs.py wait <名字> [名字...]              轮询到结束，保存 job/<名字>.result.json
  gs.py url <名字>                        打印结果链接（图片/音频/视频）
  gs.py fetch <名字> <输出文件>            下载结果（链接约 24 小时过期，要及时下载）
"""
import json, os, sys, time, urllib.request, urllib.error

BASE = 'https://saas.globalstore.ai/kyyReactApiServer'
JOB = os.environ.get('GS_JOB_DIR', 'job')
DONE = ('completed', 'failed', 'delivery_exception', 'manual_required')


def key():
    k = os.environ.get('GLOBALSTORE_API_KEY')
    if not k:
        sys.exit('请先设置环境变量 GLOBALSTORE_API_KEY')
    return k


def call(method, path, body=None):
    req = urllib.request.Request(
        BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': 'Bearer ' + key(), 'Content-Type': 'application/json'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return {'http_error': e.code, 'body': e.read().decode()[:2000]}
        except Exception as e:  # 网络抖动：退避重试
            if attempt == 3:
                return {'net_error': str(e)}
            time.sleep(2 ** attempt * 2)


def unwrap(r):
    return r['data'] if isinstance(r, dict) and isinstance(r.get('data'), dict) else r


def load(name, kind):
    return unwrap(json.load(open(os.path.join(JOB, f'{name}.{kind}.json'), encoding='utf-8')))


def result_url(name):
    u = load(name, 'result')
    return u.get('audio_url') or u.get('video_url') or u.get('image_url') or u.get('result_url')


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    os.makedirs(JOB, exist_ok=True)
    if cmd == 'balance':
        print(unwrap(call('GET', '/users/getBalance')).get('balance'))
    elif cmd == 'submit':
        name, f = sys.argv[2], sys.argv[3]
        r = call('POST', '/v2/model-center/tasks', json.load(open(f, encoding='utf-8')))
        json.dump(r, open(os.path.join(JOB, name + '.task.json'), 'w'), ensure_ascii=False, indent=1)
        u = unwrap(r)
        print(name, u.get('status'), u.get('id'), u.get('error') or r.get('body') or '')
    elif cmd == 'wait':
        pending = {n: load(n, 'task').get('id') for n in sys.argv[2:]}
        deadline = time.time() + 900
        while pending and time.time() < deadline:
            for n, tid in list(pending.items()):
                r = call('GET', '/v2/model-center/tasks/' + str(tid))
                u = unwrap(r)
                if u.get('status') in DONE or 'http_error' in r:
                    json.dump(r, open(os.path.join(JOB, n + '.result.json'), 'w'), ensure_ascii=False, indent=1)
                    print(n, u.get('status'), '扣费', u.get('amount'), u.get('error') or u.get('error_message') or '')
                    del pending[n]
            if pending:
                time.sleep(8)
        for n in pending:
            print(n, '还在跑，稍后再 wait 一次')
    elif cmd == 'url':
        print(result_url(sys.argv[2]))
    elif cmd == 'fetch':
        urllib.request.urlretrieve(result_url(sys.argv[2]), sys.argv[3])
        print(sys.argv[3], os.path.getsize(sys.argv[3]))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
