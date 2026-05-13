# hybrid_scanner


hybrid_scanner/
├── main.py                # [CLI] 서버 배포용 (시장 모드 인자를 받음)
├── main_gui.py            # [GUI] 분석/테스트용 (모드 선택 UI 포함)
├── .env                   # [보안] 텔레그램 토큰, API 키 등 저장
├── requirements.txt
│
├── core/                  # [비즈니스 로직] 데이터 가공 및 수치 연산
│   ├── __init__.py
│   ├── fetcher.py         # Config의 Market Mode에 따라 URL/경로 자동 전환
│   ├── scanner.py         # 종목 필터링 (Strategy 모듈과 협업)
│   ├── backtester.py      # 과거 진입 타점 추출
│   └── optimizer.py       # TP/SL 시뮬레이터
│
├── strategy/              # [전략 라이브러리] 캡슐화된 전략들
│   ├── __init__.py
│   ├── base.py            # 전략 추상 클래스 (와꾸 정의)
│   └── logic_loader.py    # 외부 txt/파일 로직 로드 처리
│
├── ui/                    # [인터페이스] 오직 PyQt6 관련 코드
│   ├── __init__.py
│   ├── main_window.py     # 전체 레이아웃 (KR/US 스위치 포함)
│   ├── views.py           # 테이블, 그래프 시각화 로직
│   └── threads.py         # 연산용 QThread (Fetcher, Scanner 실행)
│
├── utils/                 # [도구함] 시스템 보조
│   ├── __init__.py
│   ├── config.py          # ★ 핵심: 시장별 설정(KR/US) 로드 및 관리
│   ├── logger.py          # 분석 로그 및 에러 기록
│   └── formatter.py       # 통화(원/달러), 날짜 포맷 변환
│
└── storage/               # [DB 대용] Git 제외 대상
    ├── KR/                # 한국 시장 전용 데이터/리포트
    │   ├── raw_data/
    │   ├── reports/
    │   └── ticker_list.txt
    └── US/                # 미국 시장 전용 데이터/리포트
        ├── raw_data/
        ├── reports/
        └── ticker_list.txt