#!/usr/bin/env python3
"""把"提示词 + 参考图 + 参考音频"拼成视频任务的请求体。

用法:
  make_video_task.py <段名> <时长秒> <图片来源,逗号分隔> [音频来源,逗号分隔] [选项]

  来源可以是：已完成任务的名字（自动取它的结果链接），或直接写 http(s) 公开链接。
  提示词从 job/<段名>.prompt.txt 读取，请求体写到 job/<段名>.json。
  提示词里按顺序用"图片1、图片2…""音频1…"指代参考素材。

选项: --model sd_2.0_discount  --ratio 16:9  --res 720p
"""
import json, os, sys

JOB = os.environ.get('GS_JOB_DIR', 'job')


def resolve(src):
    if src.startswith('http'):
        return src
    r = json.load(open(os.path.join(JOB, src + '.result.json'), encoding='utf-8'))
    u = r['data'] if isinstance(r.get('data'), dict) else r
    return u.get('audio_url') or u.get('video_url') or u.get('image_url') or u.get('result_url')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = dict(zip(sys.argv[1:], sys.argv[2:]))
    if len(args) < 3:
        sys.exit(__doc__)
    name, dur, imgs = args[0], int(args[1]), args[2].split(',')
    auds = args[3].split(',') if len(args) > 3 and args[3] else []
    body = {
        'model': opts.get('--model', 'sd_2.0_discount'),
        'prompt': open(os.path.join(JOB, name + '.prompt.txt'), encoding='utf-8').read().strip(),
        'reference_images': [resolve(i) for i in imgs],
        'duration': dur,                       # 4–15 秒
        'aspect_ratio': opts.get('--ratio', '16:9'),
        'resolution': opts.get('--res', '720p'),
        'generate_audio': True,
    }
    if auds:
        body['reference_audios'] = [resolve(a) for a in auds]
    json.dump(body, open(os.path.join(JOB, name + '.json'), 'w'), ensure_ascii=False, indent=1)
    print('已写入', os.path.join(JOB, name + '.json'))


if __name__ == '__main__':
    main()
