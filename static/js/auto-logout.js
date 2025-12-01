// 자동 로그아웃 기능 (20분 = 1200초)
let inactivityTimer;
let warningTimer;
const INACTIVITY_TIME = 20 * 60 * 1000; // 20분
const WARNING_TIME = 18 * 60 * 1000;   // 18분 (2분 전 경고)

// 사용자 활동 감지 이벤트들
const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

function resetTimer() {
    clearTimeout(inactivityTimer);
    clearTimeout(warningTimer);
    
    // 경고 타이머 (18분 후)
    warningTimer = setTimeout(showWarning, WARNING_TIME);
    
    // 로그아웃 타이머 (20분 후)
    inactivityTimer = setTimeout(autoLogout, INACTIVITY_TIME);
}

function showWarning() {
    const remainingTime = Math.ceil((INACTIVITY_TIME - WARNING_TIME) / 1000);
    if (confirm(`${remainingTime}초 후 자동 로그아웃됩니다.\n계속 이용하시겠습니까?`)) {
        resetTimer(); // 사용자가 확인하면 타이머 재설정
    }
}

function autoLogout() {
    alert('20분간 비활성으로 인해 자동 로그아웃됩니다.');
    window.location.href = '/logout';
}

// 자동 로그아웃 초기화 함수
function initAutoLogout() {
    resetTimer();
    
    // 모든 사용자 활동에 대해 타이머 재설정
    events.forEach(function(event) {
        document.addEventListener(event, resetTimer, true);
    });
}

// 페이지 로드 시 자동 실행
document.addEventListener('DOMContentLoaded', initAutoLogout);