#!/usr/bin/env python3
"""앱스토어 제출용 스크린샷 만들기 (6.9인치 = 1320x2868).

애플은 6.9인치(아이폰 16/17 Pro Max) 규격을 필수로 요구한다. 저장소의
screenshot*.png 는 플레이 스토어용 6.3인치(1206x2622)라 그대로는 못 올린다.
가로세로 비율이 같아서(1206/2622 == 1320/2868) 잘림 없이 늘리기만 하면 된다.

⚠️ 이건 임시본이다. 시뮬레이터에서 'iPhone 17 Pro Max' 로 앱을 띄워 ⌘S 로 직접
   찍으면 1320x2868 원본이 나오고, 무엇보다 **실제 iOS 앱 화면**이라 훨씬 낫다.
   (지금 파일들은 안드로이드/웹 화면을 찍은 것이다)

실행: python3 scripts/build-appstore-shots.py
결과: appstore/ios-6.9-1..5.png   (.gitignore 대상 — 언제든 다시 만들 수 있다)
"""
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit('Pillow 가 필요합니다:  pip install pillow')

W, H = 1320, 2868
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'appstore')
os.makedirs(OUT, exist_ok=True)

made = 0
for i in range(1, 6):
    src = os.path.join(ROOT, f'screenshot{i}.png')
    if not os.path.exists(src):
        sys.exit(f'{src} 가 없습니다')
    im = Image.open(src).convert('RGB')
    if abs(im.width / im.height - W / H) > 0.002:
        sys.exit(f'screenshot{i}.png 의 비율({im.width}x{im.height})이 달라 '
                 f'잘림 없이 {W}x{H} 로 늘릴 수 없습니다')
    dst = os.path.join(OUT, f'ios-6.9-{i}.png')
    im.resize((W, H), Image.LANCZOS).save(dst, 'PNG', optimize=True)
    print(f'{os.path.relpath(dst, ROOT)}  {W}x{H}  {os.path.getsize(dst)//1024}KB')
    made += 1

print(f'\n{made}장 완료 — App Store Connect 의 6.9" 자리에 올리세요.')
