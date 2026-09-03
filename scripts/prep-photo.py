# 강사 사진을 홈페이지 규격(세로 3:4, 600×800, JPG)으로 맞춘다 — 어떤 크기·비율로 받아도 얼굴이 위쪽 가운데 오게 잘라 instructors/ 폴더에 저장
# 사용법: python scripts/prep-photo.py 받은사진.jpg hong-gildong  →  instructors/hong-gildong.jpg
import os, sys
from PIL import Image, ImageOps

if len(sys.argv) < 3:
    print('사용법: python scripts/prep-photo.py <받은 사진 파일> <영문이름>'); sys.exit(1)
src, slug = sys.argv[1], sys.argv[2].lower().replace(' ', '-')
out_dir = os.path.join(os.path.dirname(__file__), '..', 'instructors')
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, f'{slug}.jpg')

im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
# 세로 3:4로 자르되 얼굴이 보통 위쪽에 있으므로 위에서 35% 지점을 기준으로 맞춘다
im = ImageOps.fit(im, (600, 800), method=Image.LANCZOS, centering=(0.5, 0.35))
im.save(out, 'JPEG', quality=82, optimize=True, progressive=True)
kb = os.path.getsize(out) // 1024
print(f'저장: instructors/{slug}.jpg (600×800, {kb}KB)')
print(f'instructors.json의 photo 값: "instructors/{slug}.jpg"')
