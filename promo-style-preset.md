# 🎬 IM VOCA 홍보영상 제작 규격 (고정 프리셋)

> 힉스필드로 홍보 쇼츠를 만들 때 항상 적용하는 규격. 새 세션에서도 이 파일 기준으로 제작.

## 캐릭터 (인물 고정)
| 용도 | ID | 타입 |
|---|---|---|
| **한국 20대 여성 (메인)** | `e96f7c8b-5b83-4965-89af-8db8b1ce2acd` | image_job (힉스필드 생성 이미지) — `medias[].value`에 그대로 사용 ✅ 검증됨 |
| 보조(업로드 사진 3장, 이전 배치) | `d73d5a6f-…936f` / `2d8ecaef-…cecb` / `75cb48e9-…9ac5` | media_input |

- 사용법: `generate_video`/`generate_image`의 `medias: [{role:"image_references", value:"<ID>"}]`
- 프롬프트에 "the SAME Korean woman as the attached reference (exact face and hairstyle throughout)" 명시

## 공통 스타일
- **배경**: Korean private academy office, bright indoor light (밝은 한국 학원 사무실)
- **화면비**: 9:16 세로 쇼츠 · 15초 표준 · 1080p
- **대사**: 전부 한국어 (ALL spoken dialogue MUST be in Korean)
- **화면 텍스트**: 최소화, 영문/숫자만 (한글은 편집에서 자막으로)
- **앱 UI/로고**: AI로 그리게 하지 말 것 — 실제 스크린샷/로고(2.png)를 참조·PIP로
- **NEGATIVE**: no English speech, no English dialogue, no foreign language, cartoon, illustration, different person, face morphing, garbled text, watermark

## 대사 작성 규칙 (TTS/영상 발음)
- **발음 문제 있는 단어는 한글 발음대로 표기**해서 프롬프트/TTS에 넣기
  - 예: 붙이고→**부치고** · PDRN→**피디알엔** · IM VOCA→**아이엠 보카**
- 자막(화면 표기)은 원래 표기로, 발음용 대본만 한글 발음 표기

## 후반 작업 (로컬 ffmpeg — 카카오톡 호환)
- **자막 굽기**: `ass=` 필터 사용 (`subtitles=` 아님)
- **카톡 호환 인코딩**: `faststart` + H.264 **Main** 프로파일 + **스테레오 AAC**
- 원커맨드 템플릿:
```bash
ffmpeg -i in.mp4 -vf "ass=subs.ass" \
  -c:v libx264 -profile:v main -pix_fmt yuv420p \
  -c:a aac -ac 2 -b:a 192k \
  -movflags +faststart out.mp4
```
- 자막 없이 인코딩만 할 땐 `-vf "ass=..."` 줄만 빼기

## 제작 파이프라인 요약
1. 캐릭터 ID + 스타일 블록으로 `seedance_2_0` 15s 렌더 (한국어 대사는 따옴표로 비트별 삽입)
2. 렌더당 135크레딧 — 실행 전 잔액 확인·동의
3. 자막은 한글 오버레이 시트로 산출 → 로컬에서 ass 굽기 → 카톡 호환 인코딩
