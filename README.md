# 🚀 하이브리드 스캐너 (Hybrid Scanner V2)

한국(KR) 및 미국(US) 시장을 아우르는 퀀트 기반 주식 스캐너 및 자동화 프레임워크입니다.

## 📂 프로젝트 구조

```text
hybrid_scanner/
├── main.py                # [CLI] 서버 배포용 (시장 모드 설정 가능)
├── main_gui.py            # [GUI] 로컬 분석/테스트용 (PyQt6)
├── .env                   # [보안] API 키 및 텔레그램 설정
├── core/                  # [비즈니스 로직] 데이터 처리 및 연산
│   ├── fetcher.py         # 데이터 수집 (KR/US 자동 전환)
│   ├── scanner.py         # 전략 필터링 엔진
│   ├── backtester.py      # 과거 진입 타점 분석
│   └── optimizer.py       # TP/SL 최적화
├── strategy/              # [전략 라이브러리] 캡슐화된 전략들
│   ├── base.py            # 전략 추상 클래스
│   └── logic_loader.py    # 외부 로직 로드 처리
├── ui/                    # [인터페이스] PyQt6 관련 코드
│   ├── main_window.py     # 메인 레이아웃
│   ├── views.py           # 데이터 시각화
│   └── threads.py         # 비동기 처리 쓰레드
├── utils/                 # [도구함] 시스템 보조
│   ├── config.py          # 시장별 설정(KR/US) 로드 및 관리
│   ├── logger.py          # 실행 로그 기록
│   └── formatter.py       # 통화/날짜 포맷 변환
└── storage/               # [데이터 저장소] (Git 제외 대상)
    ├── KR/                # 한국 시장 데이터/리포트
    └── US/                # 미국 시장 데이터/리포트
    
🛠 주요 기능
멀티 마켓 지원: 환경 변수 설정으로 한국/미국 시장 즉시 전환 가능

전략 최적화: 과거 데이터를 기반으로 한 최적의 익절/손절가 산출

GUI 테스트 베드: PyQt6 기반의 직관적인 분석 도구 제공

서버 자동화: CLI 모드를 통한 정기적 리포트 생성 및 전송 가능