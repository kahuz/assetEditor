# assetEditor

Dear PyGui + Pillow/OpenCV 기반의 간단한 이미지 View 도구입니다.
`AGENTS.md`의 구현 규칙에 맞춰 클래스 기반으로 구성했습니다.

## UI 설계
r
```text
+--------------------------------------------------------------------------------+
| assetEditor                                                        파일  편집   |
+--------------------------------------------------------------------------------+
| +----------------------------+ +-----------------------------------------------+ |
| | 도구                       | | View                                        | |
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
| | View                     | |                                               | |
| | [ ] 그레이스케일 ?         | |                                               | |
| | [ ] 엣지 View ?          | |                                               | |
| | [ ] 확대 ?                 | |                                               | |
| | [====|-----]               | |                                               | |
| |                            | |                                               | |
| | 이미지 정보                | |                                               | |
| | filename.png               | |                                               | |
| | 원본: 1024 x 1024          | |                                               | |
| | View: 960 x 640          | |                                               | |
| +----------------------------+ +-----------------------------------------------+ |
| 준비됨                                                                         |
+--------------------------------------------------------------------------------+
```

## 기능

- 이미지 열기: PNG, JPG, JPEG, WEBP, BMP
- 이미지 저장: PNG, JPG, WEBP 등 Pillow가 지원하는 포맷
- 최근 이미지 히스토리 cache 저장 및 다음 실행 시 복원
- 이미지 열기 dialog 시작 폴더를 최근 이미지 폴더 기준으로 설정
- View 모드: 원본, 그레이스케일
- OpenCV View: Canny edge preview
- 체크박스로 활성화하는 View 확대/축소
- 확대 활성화 상태에서 View 영역 마우스 휠 확대/축소
- View 휠 확대 중에만 앱/View 스크롤 휠 동작 차단
- 배경 투명 처리: 단일/드래그 RGB 컬러, 유사 색상 허용치, 사각형 영역 RGB 컬러, 클릭 영역 flood fill
- 영역 선택 제외 모드: 세부 연결 영역, 사각형, 자유형 제외 방식
- PNG/WEBP 저장 시 alpha 보존, JPG/JPEG 저장 시 RGB 변환 저장
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
|   |   |-- image_preview_processor.py # View 처리
|   |   `-- preview_options.py      # View 옵션 상태
|   |-- transparency/
|   |   |-- image_transparency_processor.py # 투명 처리 도메인 로직
|   |   `-- transparency_selection.py      # 투명 처리 선택 상태
|   `-- ui/
|       `-- help_widget.py          # 도움말 UI 위젯
|-- tests/
|   `-- test_transparency_workflow.py # 투명 처리 스모크 테스트
|-- requirements.txt                # 런타임 의존성
|-- README.md                       # 설계와 실행 방법
`-- LICENSE
```
