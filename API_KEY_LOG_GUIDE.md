# API 키 확인 로그 추가 가이드

## 개요
서버 시작 시 OpenAI API 키 설정 상태를 확인하는 로그를 추가하려면 `web_app.py` 파일을 수정해야 합니다.

## 수정 위치
파일: `g:\company_project_system\web_app.py`
라인: 6026-6028 사이 (서버 시작 부분 바로 전)

## 추가할 코드

```python
    # OpenAI API 키 설정 상태 확인
    print("\n=== OpenAI API 키 설정 확인 ===")
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        # 보안을 위해 키의 일부만 표시
        masked_key = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 11 else "***"
        print(f"✓ OpenAI API 키 설정됨: {masked_key}")
        print(f"  - 키 길이: {len(api_key)} 문자")
        if api_key.startswith('sk-'):
            print("  - 키 형식: 유효 (sk-로 시작)")
        else:
            print("  - ⚠️  경고: API 키가 'sk-'로 시작하지 않습니다. 올바른 키인지 확인하세요.")
    else:
        print("✗ Open AI API 키가 설정되지 않았습니다")
        print("  - .env 파일에 OPENAI_API_KEY를 설정하거나")
        print("  - 시스템 환경 변수로 설정해주세요")
        print("  - AI 기업 분석 기능을 사용하려면 API 키가 필요합니다")
```

## 수정 방법 (옵션 1: 수동으로 추가)

1. VS Code나 메모장으로 `web_app.py` 파일을 엽니다
2. 6026번 라인 근처에서 다음 내용을 찾습니다:
   ```python
   print(f"✗ 영업 파이프라인 테이블 초기화 실패: {e}")
   
   # 서버 시작
   ```
3. 그 사이에 위의 "추가할 코드"를 복사해서 붙여넣습니다
4. 파일을 저장합니다

## 수정 방법 (옵션 2: 이 기능 건너뛰기)

API 키 확인 로그는 선택사항입니다. 이 기능 없이도:
- `.env` 파일에 API키를 설정하면 자동으로 로드됩니다
- AI 분석 기능은 정상 작동합니다
- 다만 서버 시작 시 API 키 설정 상태를 콘솔에서 바로 확인할 수 없을 뿐입니다

## 확인 방법

수정 후 서버를 재시작하면 다음과 같은 로그를 볼 수 있습니다:

**API 키가 설정된 경우:**
```
=== OpenAI API 키 설정 확인 ===
✓ OpenAI API 키 설정됨: sk-proj...abc1
  - 키 길이: 56 문자
  - 키 형식: 유효 (sk-로 시작)
```

**API 키가 설정되지 않은 경우:**
```
=== OpenAI API 키 설정 확인 ===
✗ OpenAI API 키가 설정되지 않았습니다
  - .env 파일에 OPENAI_API_KEY를 설정하거나
  - 시스템 환경 변수로 설정해주세요
  - AI 기업 분석 기능을 사용하려면 API 키가 필요합니다
```
