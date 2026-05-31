# assetEditor

Dear PyGui + Pillow/OpenCV 기반의 간단한 이미지 프리뷰 도구입니다.
`AGENTS.md`의 구현 규칙에 맞춰 클래스 기반으로 구성했습니다.

## UI 설계

```text
+--------------------------------------------------------------------------------+
| assetEditor                                                        파일  편집   |
+--------------------------------------------------------------------------------+
| +----------------------------+ +-----------------------------------------------+ |
| | 도구                       | | 프리뷰                                        | |
| |----------------------------| |-----------------------------------------------| |
| | [ 이미지 열기 ] ?          | |                                               | |
| | [ 다른 이름으로 저장 ] ?   | |              image preview                    | |
| | [ 초기화 ] ?               | |                                               | |
| |                            | |                                               | |
| | 최근 이미지                | |                                               | |
| | [ path/to/image.png v ] ?   | |                                               | |
| | [ 히스토리 열기 ] ?        | |                                               | |
| | [ 히스토리 비우기 ] ?      | |                                               | |
| |                            | |                                               | |
| | 프리뷰                     | |                                               | |
| | [ ] 그레이스케일 ?         | |                                               | |
| | [ ] 엣지 프리뷰 ?          | |                                               | |
| | [ ] 확대 ?                 | |                                               | |
| | [====|-----]               | |                                               | |
| |                            | |                                               | |
| | 이미지 정보                | |                                               | |
| | filename.png               | |                                               | |
| | 원본: 1024 x 1024          | |                                               | |
| | 프리뷰: 960 x 640          | |                                               | |
| +----------------------------+ +-----------------------------------------------+ |
| 준비됨                                                                         |
+--------------------------------------------------------------------------------+
```

## 기능

- 이미지 열기: PNG, JPG, JPEG, WEBP, BMP
- 이미지 저장: PNG, JPG, WEBP 등 Pillow가 지원하는 포맷
- 최근 이미지 히스토리 cache 저장 및 다음 실행 시 복원
- 프리뷰 모드: 원본, 그레이스케일
- OpenCV 프리뷰: Canny edge preview
- 체크박스로 슬라이더 조작을 잠글 수 있는 프리뷰 확대/축소
- 각 기능별 `?` 도움말 툴팁
- 한글 UI 표시: UTF-8 소스와 한글 폰트 range 적용

## 실행

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src\asset_editor_application.py
```

## 구조

```text
.
|-- AGENTS.md                  # 파이썬 구현 규칙
|-- .editorconfig              # UTF-8 저장 규칙
|-- .vscode/
|   |-- launch.json            # venv 기반 실행 설정
|   `-- settings.json          # VS Code UTF-8/인터프리터 설정
|-- .cache/                    # 실행 중 생성되는 히스토리 cache
|-- src/
|   |-- asset_editor_application.py # Dear PyGui 앱 진입점
|   |-- common.py                   # 공통 상수
|   |-- document/
|   |   `-- image_document.py       # 이미지 로드/저장 도메인
|   |-- fonts/
|   |   `-- korean_font_manager.py  # 한글 폰트 등록
|   |-- history/
|   |   `-- image_history_cache.py  # 최근 이미지 cache
|   |-- preview/
|   |   |-- image_preview_processor.py # 프리뷰 처리
|   |   `-- preview_options.py      # 프리뷰 옵션 상태
|   `-- ui/
|       `-- help_widget.py          # 도움말 UI 위젯
|-- requirements.txt                # 런타임 의존성
|-- README.md                       # 설계와 실행 방법
`-- LICENSE
```
